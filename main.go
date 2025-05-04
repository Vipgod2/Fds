package main

import (
	"fmt"
	"log"
	"strconv"
	"strings"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api"
)

var botToken = "7666600493:AAFnPpaPZXweKkG0IigZPf3F2G_1JksGfjY"

var (
	isForwarding    bool
	cancelChannelID int64
)

func main() {
	startBot()
}

func startBot() {
	bot, err := tgbotapi.NewBotAPI(botToken)
	if err != nil {
		log.Fatal(err)
	}
	bot.Debug = true

	fmt.Printf("Authorized on account %s\n", bot.Self.UserName)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates, _ := bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message != nil && update.Message.IsCommand() {
			if update.Message.Command() == "kidilo" {
				handleCommand(update, bot)
			}
		} else if update.CallbackQuery != nil {
			handleCallbackQuery(update.CallbackQuery, bot)
		}
	}
}

func handleCommand(update tgbotapi.Update, bot *tgbotapi.BotAPI) {
	args := strings.Fields(update.Message.CommandArguments())
	if len(args) != 1 {
		bot.Send(tgbotapi.NewMessage(update.Message.Chat.ID, "❌ Usage: /kidilo <message_link>"))
		return
	}

	link := args[0]
	chatUsername, msgID, err := extractChatAndMessageID(link)
	if err != nil {
		bot.Send(tgbotapi.NewMessage(update.Message.Chat.ID, "❌ Invalid message link format."))
		return
	}

	isForwarding = true
	cancelChannelID = update.Message.Chat.ID

	cancelBtn := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("❌ Cancel", "cancel_forward"),
		),
	)

	startMsg := tgbotapi.NewMessage(update.Message.Chat.ID, fmt.Sprintf("⏩ Starting to forward from @%s, message ID: %d", chatUsername, msgID))
	startMsg.ReplyMarkup = cancelBtn
	bot.Send(startMsg)

	// Forward messages one by one
	for id := msgID; isForwarding; id++ {
		fwd := tgbotapi.NewForward(update.Message.Chat.ID, "@"+chatUsername, id)
		_, err := bot.Send(fwd)
		if err != nil {
			bot.Send(tgbotapi.NewMessage(update.Message.Chat.ID, fmt.Sprintf("⚠️ Stopped at message %d: %v", id, err)))
			break
		}
		time.Sleep(time.Second)
	}

	bot.Send(tgbotapi.NewMessage(update.Message.Chat.ID, "✅ Forwarding complete."))
}

func handleCallbackQuery(cb *tgbotapi.CallbackQuery, bot *tgbotapi.BotAPI) {
	if cb.Data == "cancel_forward" && cb.Message.Chat.ID == cancelChannelID {
		isForwarding = false
		edit := tgbotapi.NewEditMessageText(cb.Message.Chat.ID, cb.Message.MessageID, "❌ Forwarding cancelled.")
		bot.Send(edit)
	}
}

func extractChatAndMessageID(link string) (string, int, error) {
	// Accepts formats like https://t.me/channel_name/1234
	if !strings.Contains(link, "t.me/") {
		return "", 0, fmt.Errorf("invalid link")
	}
	parts := strings.Split(link, "/")
	if len(parts) < 5 {
		return "", 0, fmt.Errorf("invalid format")
	}
	username := parts[3]
	messageID, err := strconv.Atoi(parts[4])
	if err != nil {
		return "", 0, fmt.Errorf("invalid message id")
	}
	return username, messageID, nil
}
