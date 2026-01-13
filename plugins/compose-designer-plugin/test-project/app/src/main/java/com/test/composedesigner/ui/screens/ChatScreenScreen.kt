package com.test.composedesigner.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.test.composedesigner.ui.theme.ComposeDesignerTestTheme

/**
 * Represents a chat message with sender information and content.
 */
data class ChatMessage(
    val id: Int,
    val text: String,
    val timestamp: String,
    val isFromCurrentUser: Boolean,
    val senderInitial: String? = null,
    val senderName: String? = null,
    val imageResId: Int? = null
)

/**
 * Chat screen displaying conversation messages with input field.
 *
 * Displays a list of chat messages in a conversation format with alternating
 * message bubbles for sent and received messages, along with a text input
 * field at the bottom for composing new messages.
 *
 * @param modifier Modifier to be applied to the screen
 * @param chatTitle Title displayed in the top app bar
 * @param messages List of chat messages to display
 * @param messageText Current text in the message input field
 * @param onMessageTextChange Callback when message text changes
 * @param onSendClick Callback when send button is clicked
 * @param onBackClick Callback when back button is clicked
 * @param onAttachClick Callback when attachment button is clicked
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreenScreen(
    modifier: Modifier = Modifier,
    chatTitle: String = "Chat",
    messages: List<ChatMessage> = emptyList(),
    messageText: String = "",
    onMessageTextChange: (String) -> Unit = {},
    onSendClick: () -> Unit = {},
    onBackClick: () -> Unit = {},
    onAttachClick: () -> Unit = {}
) {
    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = chatTitle,
                        style = MaterialTheme.typography.titleLarge
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(
                            imageVector = Icons.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                },
                actions = {
                    IconButton(onClick = {}) {
                        Icon(
                            imageVector = Icons.Filled.Search,
                            contentDescription = "Search"
                        )
                    }
                    IconButton(onClick = {}) {
                        Icon(
                            imageVector = Icons.Filled.MoreVert,
                            contentDescription = "More options"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface,
                    navigationIconContentColor = MaterialTheme.colorScheme.onSurface,
                    actionIconContentColor = MaterialTheme.colorScheme.onSurface
                )
            )
        },
        bottomBar = {
            MessageInputBar(
                messageText = messageText,
                onMessageTextChange = onMessageTextChange,
                onSendClick = onSendClick,
                onAttachClick = onAttachClick
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            items(messages) { message ->
                MessageBubble(message = message)
            }
        }
    }
}

/**
 * Individual message bubble component.
 *
 * @param message The chat message to display
 */
@Composable
private fun MessageBubble(
    message: ChatMessage,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isFromCurrentUser) {
            Arrangement.End
        } else {
            Arrangement.Start
        }
    ) {
        if (!message.isFromCurrentUser && message.senderInitial != null) {
            Surface(
                shape = CircleShape,
                color = MaterialTheme.colorScheme.surfaceVariant,
                modifier = Modifier.size(32.dp)
            ) {
                Box(
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = message.senderInitial,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Spacer(modifier = Modifier.width(8.dp))
        }

        Column(
            horizontalAlignment = if (message.isFromCurrentUser) {
                Alignment.End
            } else {
                Alignment.Start
            }
        ) {
            if (!message.isFromCurrentUser && message.senderName != null) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = message.senderName,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    if (message.timestamp.isNotEmpty()) {
                        Text(
                            text = message.timestamp,
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                Spacer(modifier = Modifier.height(4.dp))
            }

            Surface(
                shape = RoundedCornerShape(
                    topStart = 18.dp,
                    topEnd = 18.dp,
                    bottomStart = if (message.isFromCurrentUser) 18.dp else 4.dp,
                    bottomEnd = if (message.isFromCurrentUser) 4.dp else 18.dp
                ),
                color = if (message.isFromCurrentUser) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.surfaceVariant
                },
                modifier = Modifier.widthIn(max = 260.dp)
            ) {
                Column(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp)
                ) {
                    Text(
                        text = message.text,
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (message.isFromCurrentUser) {
                            MaterialTheme.colorScheme.onPrimary
                        } else {
                            MaterialTheme.colorScheme.onSurface
                        }
                    )
                }
            }

            if (message.isFromCurrentUser && message.timestamp.isNotEmpty()) {
                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = message.timestamp,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

/**
 * Bottom input bar for composing messages.
 *
 * @param messageText Current text in the input field
 * @param onMessageTextChange Callback when text changes
 * @param onSendClick Callback when send button is clicked
 * @param onAttachClick Callback when attachment button is clicked
 */
@Composable
private fun MessageInputBar(
    messageText: String,
    onMessageTextChange: (String) -> Unit,
    onSendClick: () -> Unit,
    onAttachClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp
    ) {
        Column(
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                TextField(
                    value = messageText,
                    onValueChange = onMessageTextChange,
                    modifier = Modifier.weight(1f),
                    placeholder = {
                        Text(
                            text = "Message #composers",
                            style = MaterialTheme.typography.bodySmall
                        )
                    },
                    colors = TextFieldDefaults.colors(
                        focusedContainerColor = MaterialTheme.colorScheme.surface,
                        unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                        focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                        unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent
                    ),
                    shape = RoundedCornerShape(24.dp),
                    maxLines = 1,
                    singleLine = true
                )

                IconButton(
                    onClick = onSendClick,
                    enabled = messageText.isNotBlank()
                ) {
                    Icon(
                        imageVector = Icons.Filled.Send,
                        contentDescription = "Send",
                        tint = if (messageText.isNotBlank()) {
                            MaterialTheme.colorScheme.primary
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 4.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(0.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = {}) {
                    Icon(
                        imageVector = Icons.Filled.Face,
                        contentDescription = "Emoji",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp)
                    )
                }

                IconButton(onClick = onAttachClick) {
                    Icon(
                        imageVector = Icons.Filled.Add,
                        contentDescription = "Attach",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp)
                    )
                }

                IconButton(onClick = {}) {
                    Icon(
                        imageVector = Icons.Filled.Add,
                        contentDescription = "Gallery",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp)
                    )
                }

                IconButton(onClick = {}) {
                    Icon(
                        imageVector = Icons.Filled.Add,
                        contentDescription = "Camera",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp)
                    )
                }

                IconButton(onClick = {}) {
                    Icon(
                        imageVector = Icons.Filled.LocationOn,
                        contentDescription = "Location",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp)
                    )
                }

                Spacer(modifier = Modifier.weight(1f))
            }
        }
    }
}

/**
 * Preview for ChatScreenScreen
 */
@Preview(
    name = "ChatScreen Preview",
    showBackground = true,
    backgroundColor = 0xFFFFFFFF,
    device = "id:pixel_5"
)
@Composable
private fun ChatScreenScreenPreview() {
    val sampleMessages = listOf(
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

    ComposeDesignerTestTheme {
        ChatScreenScreen(
            chatTitle = "#composers",
            messages = sampleMessages,
            messageText = "",
            onMessageTextChange = {},
            onSendClick = {},
            onBackClick = {},
            onAttachClick = {}
        )
    }
}
