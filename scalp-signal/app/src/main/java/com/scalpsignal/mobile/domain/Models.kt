package com.scalpsignal.mobile.domain

data class Candle(
    val openTime: Long,
    val closeTime: Long,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val quoteVolume: Double,
    val takerBuyQuote: Double
)

enum class Direction { LONG, SHORT }
enum class SignalState { CONFIRMED, WATCH }

data class ScalpingSignal(
    val symbol: String,
    val direction: Direction,
    val state: SignalState,
    val score: Int,
    val price: Double,
    val level: Double,
    val volumeRatio: Double,
    val takerDeltaPct: Double,
    val atrPct: Double,
    val levelTouches: Int,
    val entry: Double,
    val stopLoss: Double,
    val tp1: Double,
    val tp2: Double,
    val reason: String,
    val candleOpenTime: Long,
    val generatedAt: Long = System.currentTimeMillis()
)

data class MarketCandidate(
    val symbol: String,
    val quoteVolume24h: Double,
    val priceChange24hPct: Double
)
