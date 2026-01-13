package com.test.composedesigner.test

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.test.composedesigner.ui.screens.ChatMessage
import com.test.composedesigner.ui.screens.ChatScreenScreen
import com.test.composedesigner.ui.theme.ComposeDesignerTestTheme

/**
 * Test activity for compose-designer plugin.
 * Hosts generated UI component for device validation.
 *
 * AUTO-GENERATED - DO NOT COMMIT
 */
class ComposeTestActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            var messageText by remember { mutableStateOf("") }

            val sampleMessages = remember {
                listOf(
                    ChatMessage(
                        id = 1,
                        text = "loading (it's faked but the same idea applies) 🙂\nhttps://github.com/android/compose-samples/tree/master/Jetsnack",
                        timestamp = "8:00 PM",
                        isFromCurrentUser = false,
                        senderInitial = "TB"
                    ),
                    ChatMessage(
                        id = 2,
                        text = "@allsomers Take a look at the FlowCollectionsUtils#throttle() APIs",
                        timestamp = "8:00 PM",
                        isFromCurrentUser = false,
                        senderInitial = "TB"
                    ),
                    ChatMessage(
                        id = 3,
                        text = "You can use all the same stuff!",
                        timestamp = "Today",
                        isFromCurrentUser = false,
                        senderInitial = "TB"
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
                    ),
                    ChatMessage(
                        id = 6,
                        text = "Message #composers",
                        timestamp = "",
                        isFromCurrentUser = false,
                        senderInitial = "me"
                    )
                )
            }

            ComposeDesignerTestTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ChatScreenScreen(
                        chatTitle = "#composers",
                        messages = sampleMessages,
                        messageText = messageText,
                        onMessageTextChange = { messageText = it },
                        onSendClick = { messageText = "" },
                        onBackClick = {},
                        onAttachClick = {}
                    )
                }
            }
        }
    }
}
