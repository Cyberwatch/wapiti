#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2023-2024 Cyberwatch
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import json
from typing import Optional

from bs4 import BeautifulSoup
from httpx import RequestError
from os.path import join as path_join
from urllib.parse import urljoin

from wapitiCore.net import Request
from wapitiCore.attack.cms.cms_common import CommonCMS, MSG_TECHNO_VERSIONED
from wapitiCore.net.response import Response
from wapitiCore.definitions.fingerprint_webapp import SoftwareVersionDisclosureFinding
from wapitiCore.definitions.fingerprint import SoftwareNameDisclosureFinding
from wapitiCore.main.log import log_blue

MSG_NO_SPIP = "No SPIP Detected"


class ModuleSpipEnum(CommonCMS):
    """Detect SPIP version."""
    PAYLOADS_HASH = "spip_hash_files.json"
    PAYLOADS_FILE_PLUGINS = "spip_plugins.txt"
    versions = []
    plugins_list = []

    async def check_spip_plugins(self, url, plugins_file):
        """
        Check if specific SPIP extensions are installed on the given URL.
        """
        installed_plugins = []
        plugins_folders = ['plugins/', 'plugins-dist/']

        # Create a request to check with a known non-existent plugin
        no_plugin_url = urljoin(url, "plugins/non_existing_plugin/")
        no_plugin_request = Request(f'{no_plugin_url}', 'GET')

        try:
            no_plugin_response: Response = await self.crawler.async_send(no_plugin_request, follow_redirects=True)
            if no_plugin_response.status == 403:
                # If the no_plugin_response returns 403, assume all folder requests return 403
                return []
        except RequestError:
            self.network_errors += 1
            return []

        # Read plugin list once
        try:
            with open(
                    path_join(self.DATA_DIR, self.PAYLOADS_FILE_PLUGINS),
                    errors="ignore",
                    encoding='utf-8'
            ) as plugins_list:
                plugins = [plugin.strip() for plugin in plugins_list]
        except FileNotFoundError:
            print(f"Error: File '{plugins_file}' not found.")
            return []

        async def check_plugin(plugin):
            """ Check plugin folders sequentially, skipping 'plugins-dist/' if 'plugins/' gives 403 """
            for folder in plugins_folders:
                ext_url = urljoin(url, f"{folder}{plugin}/")
                request = Request(f'{ext_url}', 'GET')
                try:
                    response: Response = await self.crawler.async_send(request, follow_redirects=True)
                    if response.status == 403:
                        return plugin  # Found, skip next folder
                except RequestError:
                    self.network_errors += 1
                    continue

            return None  # Not found

        # Sequentially process each plugin
        for plugin in plugins:
            result = await check_plugin(plugin)
            if result:
                installed_plugins.append(result)

        return installed_plugins


    async def check_spip(self, url):

        request = Request(f'{url}', 'GET')
        try:
            response: Response = await self.crawler.async_send(request, follow_redirects=True)
        except RequestError:
            self.network_errors += 1
        else:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Check for SPIP-related HTML elements, classes, or attributes
            spip_elements = soup.find_all(['spip', 'your_spip_class', 'your_spip_attribute'])

            # Check for SPIP-specific meta tags
            spip_meta_tags = soup.find_all('meta', {'name': ['generator', 'author'], 'content': 'SPIP'})

            # Check for SPIP-specific HTTP headers
            spip_http_headers = {'X-Spip-Cache', 'X-Spip-Version'}  # Add more headers if needed
            has_spip_headers = any(header.lower() in response.headers for header in spip_http_headers)

            # Check for common SPIP directories or files
            common_spip_paths = ['/ecrire/', '/squelettes/']
            has_spip_paths = any(path in response.content for path in common_spip_paths)

            has_spip_in_headers = 'composed-by' in response.headers and 'SPIP' in response.headers['composed-by']

            # Check if any of the SPIP indicators were found
            return spip_elements or spip_meta_tags or has_spip_headers or has_spip_paths or has_spip_in_headers


    
    async def attack(self, request: Request, response: Optional[Response] = None):
        self.finished = True
        request_to_root = Request(request.url)

        if await self.check_spip(request_to_root.url):
            await self.detect_version(self.PAYLOADS_HASH, request_to_root.url)  # Call the method on the instance
            self.versions = sorted(self.versions, key=lambda x: x.split('.')) if self.versions else []
            self.plugins_list = await self.check_spip_plugins(request_to_root.url, self.PAYLOADS_FILE_PLUGINS)

            spip_detected = {
                "name": "SPIP",
                "versions": self.versions,
                "categories": ["CMS SPIP"],
                "groups": ["Content"]
            }

            log_blue(
                MSG_TECHNO_VERSIONED,
                "SPIP",
                self.versions
            )

            if self.versions:
                await self.add_info(
                    finding_class=SoftwareVersionDisclosureFinding,
                    request=request_to_root,
                    info=json.dumps(spip_detected),
                )
            await self.add_info(
                finding_class=SoftwareNameDisclosureFinding,
                request=request_to_root,
                info=json.dumps(spip_detected),
            )
            if self.plugins_list:
                for plugin in self.plugins_list:
                    plugin_detected = {
                        "name": plugin,
                        "versions": [],
                        "categories": ["SPIP Plugin"],
                        "groups": ['Add-ons']
                    }
                    log_blue(
                        MSG_TECHNO_VERSIONED,
                        plugin,
                        []
                    )
                    await self.add_info(
                        finding_class=SoftwareNameDisclosureFinding,
                        request=request,
                        info=json.dumps(plugin_detected),
                        response=response
                    )


        else:
            log_blue(MSG_NO_SPIP)
