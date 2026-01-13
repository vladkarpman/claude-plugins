package com.test.composedesigner

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.test.composedesigner.ui.screens.ChatMessage
import com.test.composedesigner.ui.screens.ChatScreenScreen
import com.test.composedesigner.ui.theme.ComposeDesignerTestTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ComposeDesignerTestTheme {
                var messageText by remember { mutableStateOf("") }

                val sampleMessages = listOf(
                    ChatMessage(
                        id = 1,
                        text = "loading (it's faked but the same idea applies) 🙂\nhttps://github.com/android/compose-samples/tree/master/Jetsnack",
                        timestamp = "8:05 PM",
                        isFromCurrentUser = false,
                        senderInitial = "TB",
                        senderName = "Taylor Brooks"
                    ),
                    ChatMessage(
                        id = 2,
                        text = "@allsomers Take a look at the FlowCollectionsUtils#throttle() APIs",
                        timestamp = "",
                        isFromCurrentUser = false,
                        senderInitial = "TB",
                        senderName = null
                    ),
                    ChatMessage(
                        id = 3,
                        text = "You can use all the same stuff!",
                        timestamp = "Today",
                        isFromCurrentUser = false,
                        senderInitial = "TB",
                        senderName = null
                    ),
                    ChatMessage(
                        id = 4,
                        text = "Thank you!",
                        timestamp = "8:00 PM",
                        isFromCurrentUser = true
                    ),
                    ChatMessage(
                        id = 5,
                        text = "Check it out!",
                        timestamp = "8:00 PM",
                        isFromCurrentUser = true
                    )
                )

                ChatScreenScreen(
                    chatTitle = "#composers",
                    messages = sampleMessages,
                    messageText = messageText,
                    onMessageTextChange = { messageText = it },
                    onSendClick = {
                        messageText = ""
                    },
                    onBackClick = { finish() },
                    onAttachClick = { }
                )
            }
        }
    }
}
