package com.scalpsignal.mobile.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColors = darkColorScheme(
    primary = Color(0xFF63E6BE),
    secondary = Color(0xFF74C0FC),
    tertiary = Color(0xFFFFC078),
    background = Color(0xFF090B10),
    surface = Color(0xFF11151D),
    surfaceVariant = Color(0xFF171C26),
    onPrimary = Color(0xFF05110D),
    onBackground = Color(0xFFE8EDF6),
    onSurface = Color(0xFFE8EDF6),
    onSurfaceVariant = Color(0xFFB6C0D0),
    error = Color(0xFFFF8787)
)

@Composable
fun ScalpSignalTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = DarkColors, content = content)
}
