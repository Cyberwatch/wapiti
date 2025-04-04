import json
from unittest.mock import AsyncMock

import httpx
from httpx import RequestError
import respx
import pytest

from wapitiCore.net.classes import CrawlerConfiguration
from wapitiCore.net import Request
from wapitiCore.net.crawler import AsyncCrawler
from wapitiCore.attack.mod_network_device import ModuleNetworkDevice
from wapitiCore.attack.network_devices.mod_forti import ModuleForti
from wapitiCore.attack.network_devices.mod_harbor import ModuleHarbor


@pytest.mark.asyncio
@respx.mock
async def test_no_net_device():
    # Test no network device detected
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Vous Etes Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert not persister.add_payload.call_count


@pytest.mark.asyncio
@respx.mock
async def test_ubika_without_version():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get("http://perdu.com/app/monitor/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>UBIKA WAAP GATEWAY</title></head><body><h1>Perdu sur l'Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "UBIKA WAAP", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_ubika_with_version():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get("http://perdu.com/app/monitor/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>UBIKA WAAP GATEWAY</title></head><body><h1>Perdu sur l'Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )

    respx.get("http://perdu.com/app/monitor/api/info/product").mock(
        return_value=httpx.Response(
            200,
            content='{"result":{"api":{"version":"1.0","logLevel":"info"},\
            "appliance":{"name":"Management","role":"manager","ip":"192.168.0.169","port":3002},\
            "product":{"version":"6.5.6"}},"_info":{"apiVersion":"1.0","serverTimestamp":1708417838114,\
            "responseTime":"0s","responseStatus":200}}'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "UBIKA WAAP", "versions": ["6.5.6"], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortimanager():
    respx.get("http://perdu.com/p/login/").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <div class="sign-in-header" style="visibility: hidden"><span class="platform">FortiManager-3000G</span>'
                    '</body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "FortiManager", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_ssl_vpn():
    respx.get("http://perdu.com/remote/login?lang=en").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Login</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> '
        )
    )

    respx.get("http://perdu.com/remote/fgt_lang?lang=fr").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/javascript"},
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Fortinet SSL-VPN", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_fortinet_false_positive():
    respx.get("http://perdu.com/login/?next=/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Login</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> '
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert not persister.add_payload.call_count


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortinet():
    respx.get("http://perdu.com/login/?next=/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Fortinet</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> '
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Fortinet", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortinet_from_main_app_class():
    respx.get("http://perdu.com/login/?next=/").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>login</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> '
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Fortinet", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortiportal_from_title():
    respx.get("http://perdu.com/fpc/app/login").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>FortiPortal</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> '
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "FortiPortal", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortimail():
    respx.get("http://perdu.com/admin/").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>FortiMail</title><meta name="FortiMail" content="width=device-width, initial-scale=1">\
            </head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> '
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "FortiMail", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortimanager():
    respx.get("http://perdu.com/p/login/").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>FortiManager</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2></body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "FortiManager", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortianalyzer():
    respx.get("http://perdu.com/p/login/").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>Login</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <div class="sign-in-header">FortiAnalyzer</div></body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "FortiAnalyzer", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortinet_ssl_vpn():
    respx.get("http://perdu.com/remote/fgt_lang?lang=en").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>Login</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                <div class="sign-in-header">FortiAnalyzer</div></body></html>',
            headers={"content-type": "javascript"}
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Fortinet SSL-VPN", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"

@pytest.mark.asyncio
@respx.mock
async def test_detect_fortiweb():
    respx.get("http://perdu.com/fgt_lang.js?paths=lang/en:com_info").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>Login</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                <div class="sign-in-header">FortiAnalyzer</div></body></html>',
            headers={"content-type": "javascript"}
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "FortiWeb", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_fortgate_from_title():
    respx.get("http://perdu.com/logindisclaimer").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>Fortigate</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                <div class="sign-in-header">FortiAnalyzer</div></body></html>',
            headers={"content-type": "javascript"}
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Fortigate", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"

@pytest.mark.asyncio
@respx.mock
async def test_raise_on_request_error():
    """Tests that a RequestError is raised when calling the module with wrong URL."""

    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*").mock(
        side_effect=RequestError("RequestError occurred: [Errno -2] Name or service not known"))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleForti(crawler, persister, options, crawler_configuration)

        with pytest.raises(RequestError) as exc_info:
            await module.check_forti("http://perdu.com/")

        assert exc_info.value.args[0] == "RequestError occurred: [Errno -2] Name or service not known"


@pytest.mark.asyncio
@respx.mock
async def test_detect_harbor_with_version():
    json_data = {
        "auth_mode": "db_auth",
        "banner_message": "",
        "harbor_version": "v2.10",
        "oidc_provider_name": "",
        "primary_auth_mode": False,
        "self_registration": True
    }
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Hello</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/api/v2.0/systeminfo").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            content=json.dumps(json_data)
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Harbor", "versions": ["v2.10"], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_harbor_without_version():
    json_data = {
        "auth_mode": "db_auth",
        "banner_message": "",
        "oidc_provider_name": "",
        "primary_auth_mode": False,
        "self_registration": True
    }
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Hello</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/api/v2.0/systeminfo").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            content=json.dumps(json_data)
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Harbor", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_harbor_with_json_error():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Hello</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/api/v2.0/systeminfo").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            content="Not Json"
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Harbor", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_detect_harbor_raise_on_request_error():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Hello</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                        </body></html>'
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*").mock(
        side_effect=RequestError("RequestError occurred: [Errno -2] Name or service not known"))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleHarbor(crawler, persister, options, crawler_configuration)

        with pytest.raises(RequestError) as exc_info:
            await module.check_harbor("http://perdu.com/")

        assert exc_info.value.args[0] == "RequestError occurred: [Errno -2] Name or service not known"


@pytest.mark.asyncio
@respx.mock
async def test_detect_citrix_from_title():
    respx.get("http://perdu.com/logon/LogonPoint/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Citrix Gateway</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Citrix Gateway", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_detect_citrix_from_class():
    respx.get("http://perdu.com/logon/LogonPoint/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title class="_ctxstxt_NetscalerGateway">Hello</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "NetscalerGateway", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_detect_citrix_in_root_url():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>NetScaler ADC</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider <span>NetScaler ADC</span></h2> \
                    </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "NetScaler ADC", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_checkpoint_without_version():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get("http://perdu.com/Login/Login").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Hello</title></head><body><h1>Perdu sur l'Internet ?</h1> \
                <h2>Check Point Software Technologies Ltd</h2> \
                <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Check Point", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"

@pytest.mark.asyncio
@respx.mock
async def test_checkpoint_based_on_realmsArrJSON():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get("http://perdu.com/Login/Login").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Hello</title></head><body><h1>Perdu sur l'Internet ?</h1> \
                <h2>Hello</h2><script type='text/javascript'>var realmsArrJSON = '[]'</script> \
                <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Check Point", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"


@pytest.mark.asyncio
@respx.mock
async def test_checkpoint_with_version():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )
    respx.get("http://perdu.com/cgi-bin/home.tcl").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Login</title></head><body><h1>Perdu sur l'Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> \
                <div><script src='/login/login.js'></script></div> <script>var hostname='';var version='R80.20';</script>\
                <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Check Point", "versions": ["R80.20"], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"

@pytest.mark.asyncio
@respx.mock
async def test_detect_cve_forti():
    respx.get("http://perdu.com/login/?next=/").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><title>Fortinet</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> '
        )
    )
    respx.get("http://perdu.com/login?redir=/ng").mock(
        return_value=httpx.Response(
            200,
            content='<html class="main-app"><head><f-icon class="fa-warning></f-icon><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <div class="sign-in-header" style="visibility: hidden"><span class="platform">FortiManager-3000G</span> \
            </body></html>',
            headers={"APSCOOKIE_": "APSCOOKIE_"}
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/wapiti3-.*?").mock(return_value=httpx.Response(101, headers={"Connection": "Upgrade"}))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Fortinet", "versions": [], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[0][1]["module"] == "network_device"

        assert persister.add_payload.call_args_list[1][1]["info"] == (
            'URL http://perdu.com/ seems vulnerable to CVE-2024-55591'
        )
        assert persister.add_payload.call_args_list[1][1]["module"] == "network_device"

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_connect_in_title():
    respx.get("http://perdu.com/dana-na/auth/url_default/welcome.cgi").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Ivanti Connect Secure</title></head><body> \
            <h2>Pas de panique, on va vous aider </h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti Connect Secure", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_connect_in_frmLogin():
    respx.get("http://perdu.com/dana-na/auth/url_default/welcome.cgi").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Ivanti Connect Secure</title></head><body> \
            <h2>Pas de panique, on va vous aider <form name="frmLogin"> </form></h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti Connect Secure", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_Service_Manager_in_Title():
    respx.get("http://perdu.com/dana/home/index.cgi").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Ivanti Service Manager</title></head><body> \
            <h2>Pas de panique, on va vous aider</h2> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti Service Manager", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_Service_Manager_in_h1():
    respx.get("http://perdu.com/dana/home/index.cgi").mock(
        return_value=httpx.Response(
            200,
            content='<html><head>Vous Perdu ?<title></title></head><body> \
            <h1>Ivanti Service Manager</h1> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti Service Manager", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_Service_Manager_in_file():
    respx.get("http://perdu.com/dana/home/index.cgi").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title> \
            <script src="/lib/RespondJs/respond.min.js" type="text/javascript"></script> </head><body>\
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti Service Manager", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_User_Portal_in_Title():
    respx.get("http://perdu.com/mifs/user/login.jsp").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Ivanti User Portal</title></head><body> \
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti User Portal", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_ivanti_User_Portal_in_H1():
    respx.get("http://perdu.com/mifs/user/login.jsp").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body> \
                    <h1>MI_LOGIN_SCREEN</h1></body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Ivanti User Portal", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_detect_no_info():
    respx.get("http://perdu.com/dana/home/index.cgi").mock(
        return_value=httpx.Response(
            200,
            content='<html><head> \
            </head><body>\
                    </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html></body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 0


@pytest.mark.asyncio
@respx.mock
async def test_detect_palo_alto_in_Title():
    respx.get("http://perdu.com/global-protect/login.esp").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>GlobalProtect Portal</title></head> \
            <body><h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Palo Alto GlobalProtect Portal", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_palo_alto_in_Div():
    respx.get("http://perdu.com/global-protect/login.esp").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>perdu</title></head><body> \
                    <div id="heading">GlobalProtect Portal</div></body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    respx.post(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)
        print(module)
        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Palo Alto GlobalProtect Portal", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_palo_alto_form():
    respx.get("http://perdu.com/global-protect/login.esp").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body> \
                    <pan_form></pan_form></body></html>'
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Palo Alto GlobalProtect Portal", "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_palo_alto_version():
    respx.get("http://perdu.com/global-protect/portal/css/bootstrap.min.css").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>',
            headers=httpx.Headers({"Etag":"661c69a8-2606e"})
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Palo Alto GlobalProtect Portal", "versions": ["10.2.9-h1", "11.0.4-h1", "11.1.2-h3"], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_detect_palo_alto_version_format2():
    respx.get("http://perdu.com/global-protect/portal/css/bootstrap.min.css").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>',
            headers=httpx.Headers({"Etag":"2606e661c69a8"})
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Palo Alto GlobalProtect Portal", "versions": ["10.2.9-h1", "11.0.4-h1", "11.1.2-h3"], "categories": ["Network Equipment"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_detect_palo_alto_version_format3():
    respx.get("http://perdu.com/global-protect/portal/css/bootstrap.min.css").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body> \
                    <h2>Pas de panique, on va vous aider</h2> </body></html>',
            headers=httpx.Headers({"Etag":""})
        )
    )
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content='<html><head><title>Vous Perdu ?</title></head><body><h1>Perdu sur Internet ?</h1> \
                <h2>Pas de panique, on va vous aider</h2> </body></html>'
        )
    )

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleNetworkDevice(crawler, persister, options, crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 0
