from typing import Any
import pytest
from unittest.mock import AsyncMock, MagicMock
from openai import OpenAIError

from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.parsers.rss_parser import RSSParser
from app.infrastructure.parsers.telegram import TelegramChannelParser
from app.infrastructure.telegram.client import TelegramParserClient
from app.infrastructure.telegram.publisher import TelegramPublisher

# 1. OpenAI Generator Tests
@pytest.mark.asyncio
async def test_openai_generator_success(mocker: Any) -> None:
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [
        MagicMock(message=MagicMock(content="Generated AI Telegram Post 🎉"))
    ]
    
    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_chat_completion)
    mocker.patch("app.infrastructure.ai.openai_client.AsyncOpenAI", return_value=mock_openai_client)

    generator = OpenAIGenerator()
    result = await generator.generate_post(title="Breaking News", text="Some news content")
    assert result == "Generated AI Telegram Post 🎉"

@pytest.mark.asyncio
async def test_openai_generator_empty_response(mocker: Any) -> None:
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content=None))]
    
    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_chat_completion)
    mocker.patch("app.infrastructure.ai.openai_client.AsyncOpenAI", return_value=mock_openai_client)

    generator = OpenAIGenerator()
    with pytest.raises(RuntimeError) as exc_info:
        await generator.generate_post(title="Title", text="Text")
    assert "OpenAI returned an empty response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_openai_generator_openai_error(mocker: Any) -> None:
    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create = AsyncMock(side_effect=OpenAIError("API Rate Limit"))
    mocker.patch("app.infrastructure.ai.openai_client.AsyncOpenAI", return_value=mock_openai_client)

    generator = OpenAIGenerator()
    with pytest.raises(RuntimeError) as exc_info:
        await generator.generate_post(title="Title", text="Text")
    assert "AI Generation failed" in str(exc_info.value)

# 2. RSS Parser Tests
@pytest.mark.asyncio
async def test_rss_parser_fetch_feed_success(mocker: Any) -> None:
    sample_rss_xml = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
     <title>Sample Feed</title>
     <item>
      <title>Article 1</title>
      <link>https://example.com/article-1</link>
      <description>Description 1</description>
     </item>
    </channel>
    </rss>"""

    mock_resp = MagicMock()
    mock_resp.text = sample_rss_xml
    mock_resp.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_resp)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("httpx.AsyncClient", return_value=mock_http_client)

    parser = RSSParser()
    items = await parser.fetch_feed("https://example.com/rss.xml", limit=10)
    assert len(items) == 1
    assert items[0].title == "Article 1"
    assert items[0].url == "https://example.com/article-1"
    assert items[0].summary == "Description 1"

@pytest.mark.asyncio
async def test_rss_parser_fetch_feed_exception(mocker: Any) -> None:
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("Network error"))
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("httpx.AsyncClient", return_value=mock_http_client)

    parser = RSSParser()
    items = await parser.fetch_feed("https://example.com/bad-rss.xml")
    assert items == []

# 3. Telegram Channel Parser Tests
@pytest.mark.asyncio
async def test_telegram_channel_parser_fetch_messages(mocker: Any) -> None:
    msg1 = MagicMock(text="Message 1 about AI")
    msg2 = MagicMock(text=None) # Should be skipped
    msg3 = MagicMock(text="Message 3 about Python")

    async def mock_iter_messages(*args: Any, **kwargs: Any) -> Any:
        for msg in [msg1, msg2, msg3]:
            yield msg

    mock_parser_client = MagicMock()
    mock_parser_client.client.iter_messages = mock_iter_messages

    parser = TelegramChannelParser(mock_parser_client)
    messages = await parser.fetch_recent_messages("@testchannel", limit=10)
    assert len(messages) == 2
    assert messages[0].text == "Message 1 about AI"
    assert messages[1].text == "Message 3 about Python"

@pytest.mark.asyncio
async def test_telegram_channel_parser_fetch_messages_error(mocker: Any) -> None:
    mock_parser_client = MagicMock()
    mock_parser_client.client.iter_messages.side_effect = Exception("Channel restricted")

    parser = TelegramChannelParser(mock_parser_client)
    messages = await parser.fetch_recent_messages("@privatechannel")
    assert messages == []

def test_telegram_channel_parser_filter_by_keywords() -> None:
    parser = TelegramChannelParser(MagicMock())

    msg1 = MagicMock(text="Latest news on Artificial Intelligence and Machine Learning")
    msg2 = MagicMock(text="Today weather report is sunny")
    msg3 = MagicMock(text=None)

    # 1. No keywords -> returns all messages
    assert len(parser.filter_by_keywords([msg1, msg2], [])) == 2

    # 2. Filter with keywords
    filtered = parser.filter_by_keywords([msg1, msg2, msg3], ["intelligence", "python"])
    assert len(filtered) == 1
    assert filtered[0].text == msg1.text

# 4. Telegram Parser Client Tests
def test_telegram_parser_client_init_validation() -> None:
    with pytest.raises(ValueError):
        TelegramParserClient(api_id=0, api_hash="hash", session_string="string")

@pytest.mark.asyncio
async def test_telegram_parser_client_connect_and_authorize(mocker: Any) -> None:
    mock_tc = AsyncMock()
    mock_tc.connect = AsyncMock()
    mock_tc.is_user_authorized = AsyncMock(return_value=True)
    mock_tc.is_connected = MagicMock(return_value=True)
    mock_tc.disconnect = AsyncMock()

    mocker.patch("app.infrastructure.telegram.client.StringSession", return_value=MagicMock())
    mocker.patch("app.infrastructure.telegram.client.TelegramClient", return_value=mock_tc)

    client = TelegramParserClient(api_id=12345, api_hash="hash", session_string="dummy_session")
    
    async with client as c:
        assert c is client

    mock_tc.connect.assert_called_once()
    mock_tc.disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_telegram_parser_client_unauthorized(mocker: Any) -> None:
    mock_tc = AsyncMock()
    mock_tc.connect = AsyncMock()
    mock_tc.is_user_authorized = AsyncMock(return_value=False)
    mocker.patch("app.infrastructure.telegram.client.StringSession", return_value=MagicMock())
    mocker.patch("app.infrastructure.telegram.client.TelegramClient", return_value=mock_tc)

    client = TelegramParserClient(api_id=12345, api_hash="hash", session_string="dummy_session")
    with pytest.raises(ValueError) as exc_info:
        await client.start()
    assert "Unauthorized Telegram session" in str(exc_info.value)


# 5. Telegram Publisher Tests
@pytest.mark.asyncio
async def test_telegram_publisher_success(mocker: Any) -> None:
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.session.close = AsyncMock()
    mocker.patch("app.infrastructure.telegram.publisher.Bot", return_value=mock_bot)

    publisher = TelegramPublisher()
    res = await publisher.send_post("Hello Channel!")
    assert res is True
    mock_bot.send_message.assert_called_once()
    mock_bot.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_telegram_publisher_exception(mocker: Any) -> None:
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock(side_effect=Exception("Bot blocked"))
    mock_bot.session.close = AsyncMock()
    mocker.patch("app.infrastructure.telegram.publisher.Bot", return_value=mock_bot)

    publisher = TelegramPublisher()
    with pytest.raises(Exception) as exc_info:
        await publisher.send_post("Failed Post")
    assert "Bot blocked" in str(exc_info.value)
    mock_bot.session.close.assert_called_once()
