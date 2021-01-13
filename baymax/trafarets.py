from functools import partial

import trafaret as t


OptKey = partial(t.Key, optional=True)


Chat = t.Dict({t.Key("id"): t.Int}).allow_extra("*")
MessageEntity = t.Dict({}).allow_extra("*")
Audio = t.Dict({}).allow_extra("*")
Document = t.Dict({}).allow_extra("*")
Animation = t.Dict({}).allow_extra("*")
Game = t.Dict({}).allow_extra("*")
Photo = t.Dict({}).allow_extra("*")
Sticker = t.Dict({}).allow_extra("*")
Video = t.Dict({}).allow_extra("*")
Voice = t.Dict({}).allow_extra("*")
VideoNote = t.Dict({}).allow_extra("*")
Contact = t.Dict({}).allow_extra("*")
Venue = t.Dict({}).allow_extra("*")
PhotoSize = t.Dict({}).allow_extra("*")
Invoice = t.Dict({}).allow_extra("*")
SuccessfulPayment = t.Dict({}).allow_extra("*")
PassportData = t.Dict({}).allow_extra("*")

User = t.Dict(
    {
        t.Key("id"): t.Int,
        t.Key("is_bot"): t.Bool,
        t.Key("first_name"): t.String,
        OptKey("last_name"): t.String,
        OptKey("username"): t.String,
        OptKey(
            "language_code"
        ): t.String,  # IETF language tag of the user's language
    }
)

Location = t.Dict({t.Key("longitude"): t.Float, t.Key("latitude"): t.Float})

PollOption = t.Dict(
    {
        t.Key("text"): t.String(min_length=1, max_length=100),
        t.Key("voter_count"): t.Int,
    }
)


Poll = t.Dict(
    {
        t.Key("id"): t.String,
        t.Key("question"): t.String(min_length=1, max_length=255),
        t.Key("options"): t.List(PollOption),
        t.Key("is_closed"): t.Bool,
    }
)

MessageForward = t.Forward()
ReplyMarkupForward = t.Forward()

Message = t.Dict(
    {
        t.Key("message_id"): t.Int,
        OptKey("from"): User,
        t.Key("date"): t.Int,  # unix time
        OptKey("chat"): Chat,
        OptKey("forward_from"): User,
        OptKey("forward_from_chat"): Chat,
        OptKey("forward_signature"): t.String,
        OptKey("forward_sender_name"): t.String,
        OptKey("forward_date"): t.Int,
        OptKey("reply_to_message"): MessageForward,
        OptKey("edit_date"): t.Int,
        OptKey("media_group_id"): t.String,
        OptKey("author_signature"): t.String,
        t.Key("text", default=""): t.String(
            allow_blank=True, min_length=0, max_length=4096
        ),
        OptKey("entities"): t.List(MessageEntity),
        OptKey("caption_entities"): t.List(MessageEntity),
        OptKey("audio"): Audio,
        OptKey("document"): Document,
        OptKey("animation"): Animation,
        OptKey("game"): Game,
        OptKey("photo"): t.List(Photo),
        OptKey("sticker"): Sticker,
        OptKey("video"): Video,
        OptKey("voice"): Voice,
        OptKey("video_note"): VideoNote,
        OptKey("caption"): t.String,
        OptKey("contact"): Contact,
        OptKey("location"): Location,
        OptKey("venue"): Venue,
        OptKey("poll"): Poll,
        OptKey("new_chat_members"): t.List(User),
        OptKey("new_chat_title"): t.String,
        OptKey("new_chat_photo"): t.List(PhotoSize),
        OptKey("delete_chat_photo"): t.Bool,
        OptKey("group_chat_created"): t.Bool,
        OptKey("supergroup_chat_created"): t.Bool,
        OptKey("channel_chat_created"): t.Bool,
        OptKey("migrate_to_chat_id"): t.Int,
        OptKey("migrate_from_chat_id"): t.Int,
        OptKey("pinned_message"): MessageForward,
        OptKey("invoice"): Invoice,
        OptKey("successful_payment"): SuccessfulPayment,
        OptKey("connected_website"): t.String,  # TODO: URL or domain?
        OptKey("passport_data"): PassportData,  # TODO: URL or domain?
        OptKey("via_bot"): User,
        OptKey("reply_markup"):	ReplyMarkupForward,
    }
)

MessageForward << Message


InputTextMessageContent = t.Dict({
    t.Key("message_text"): t.String(max_length=4096),
    OptKey("parse_mode"): t.String,
    OptKey("disable_web_page_preview"): t.Bool,
})


InputMessageContent = t.Or(InputTextMessageContent)

LoginUrl = t.URL
CallbackGame = t.String

InlineKeyboardButton = t.Dict({
    t.Key("text"): t.String,
    OptKey("url"): LoginUrl,
    OptKey("callback_data"): t.String,
    OptKey("switch_inline_query"): t.String,
    OptKey("switch_inline_query_current_chat"): t.String,
    OptKey("callback_game"): CallbackGame,
    OptKey("pay"): t.Bool,
})

InlineKeyboardMarkup = t.Dict({
    t.Key("inline_keyboard"): t.List(t.List(InlineKeyboardButton))
})


# ReplyMarkup = t.Enum(InlineKeyboardMarkup)
ReplyMarkupForward << InlineKeyboardMarkup

InlineQuery = t.Dict(
    {
        t.Key("id"): t.String,
        t.Key("from"): User,
        OptKey("Location"): Location,
        t.Key("query"): t.String(allow_blank=True),
        t.Key("offset"): t.String(allow_blank=True),
    }
)


InlineQueryResultArticle = t.Dict({
    t.Key("type"):	t.String,
    t.Key("id"):	t.String,
    t.Key("title"):	t.String,
    t.Key("input_message_content"):	InputMessageContent,
    OptKey("reply_markup"):	InlineKeyboardMarkup,
    OptKey("url"):	t.String,
    OptKey("hide_url"):	t.Bool,
    OptKey("description"):	t.String,
    OptKey("thumb_url"):	t.String,
    OptKey("thumb_width"):	t.Int,
    OptKey("thumb_height"):	t.Int,
})


InlineQueryResult = t.Or(InlineQueryResultArticle)


AnswerInlineQuery = t.Dict(
    {
        t.Key("inline_query_id"): t.String,
        t.Key("results"): t.List(InlineQueryResult),
        OptKey("location"): Location,
        OptKey("cache_time"): t.Int,
        OptKey("is_personal"): t.Bool,
        OptKey("next_offset"): t.String,
        OptKey("switch_pm_text"): t.String,
        OptKey("switch_pm_parameter"): t.String,
    }
)

ChosenInlineResult = t.Dict(
    {
        t.Key("result_id"): t.String,
        t.Key("from"): User,
        OptKey("Location"): Location,
        OptKey("inline_message_id"): t.String,
        t.Key("query"): t.String,
    }
)


CallbackQuery = t.Dict(
    {
        t.Key("id"): t.String,
        t.Key("from"): User,
        t.Key("message"): Message,
        OptKey("inline_message_id"): t.String,
        t.Key("chat_instance"): t.String,
        OptKey("data"): t.String,
        OptKey("game_short_name"): t.String,
    }
)


ShippingAddress = t.Dict(
    {
        t.Key("country_code"): t.String(min_length=2, max_length=2),
        t.Key("state"): t.String,
        t.Key("city"): t.String,
        t.Key("street_line1"): t.String,
        t.Key("street_line2"): t.String,
        t.Key("post_code"): t.String,
    }
)

ShippingQuery = t.Dict(
    {
        t.Key("id"): t.String,
        t.Key("from"): User,
        t.Key("invoice_payload"): t.String,
        t.Key("shipping_address"): ShippingAddress,
    }
)

LabeledPrice = t.Dict({t.Key("label"): t.String, t.Key("amount"): t.Int})

ShippingOption = t.Dict(
    {
        t.Key("id"): t.String,
        t.Key("title"): t.String,
        t.Key("prices"): t.List(LabeledPrice),
    }
)

OrderInfo = t.Dict(
    {
        OptKey("name"): t.String,
        OptKey("phone_number"): t.String,
        OptKey("email"): t.Email,
        OptKey("order_info"): t.String,
        OptKey("shipping_address"): ShippingAddress,
    }
)


PreCheckoutQuery = t.Dict(
    {
        t.Key("id"): t.String,
        t.Key("from"): User,
        t.Key("currency"): t.String(min_length=3, max_length=3),
        t.Key("total_amount"): t.Int,
        t.Key("invoice_payload"): t.String,
        OptKey("shipping_option_id"): t.String,
        OptKey("order_info"): OrderInfo,
    }
)

Update = t.Dict(
    {
        t.Key("update_id"): t.Int,
        OptKey("message"): Message,
        OptKey("edited_message"): Message,
        OptKey("channel_post"): Message,
        OptKey("edited_channel_post"): Message,
        OptKey("inline_query"): InlineQuery,
        OptKey("chosen_inline_result"): ChosenInlineResult,
        OptKey("callback_query"): CallbackQuery,
        OptKey("shipping_query"): ShippingQuery,
        OptKey("pre_checkout_query"): PreCheckoutQuery,
        OptKey("Poll"): Poll,
    }
)
