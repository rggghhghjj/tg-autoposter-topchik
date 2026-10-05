package com.scalpsignal.mobile.data

import com.scalpsignal.mobile.domain.Candle
import com.scalpsignal.mobile.domain.MarketCandidate
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.io.IOException
import java.util.concurrent.TimeUnit

class BinanceApi(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(8, TimeUnit.SECONDS)
        .callTimeout(12, TimeUnit.SECONDS)
        .build()
) {
    private val baseUrl = "https://fapi.binance.com"

    suspend fun loadUniverse(minQuoteVolume24h: Double): List<MarketCandidate> = withContext(Dispatchers.IO) {
        val raw = get("$baseUrl/fapi/v1/ticker/24hr")
        val arr = JSONArray(raw)
        buildList {
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                val symbol = o.optString("symbol")
                val quoteVolume = o.optString("quoteVolume").toDoubleOrNull() ?: continue
                val changePct = o.optString("priceChangePercent").toDoubleOrNull() ?: 0.0
                if (symbol.endsWith("USDT") && quoteVolume >= minQuoteVolume24h) {
                    add(MarketCandidate(symbol, quoteVolume, changePct))
                }
            }
        }.sortedByDescending { it.quoteVolume24h }
    }

    suspend fun loadKlines(symbol: String, interval: String = "1m", limit: Int = 120): List<Candle> =
        withContext(Dispatchers.IO) {
            val raw = get("$baseUrl/fapi/v1/klines?symbol=$symbol&interval=$interval&limit=$limit")
            val arr = JSONArray(raw)
            buildList {
                for (i in 0 until arr.length()) {
                    val k = arr.getJSONArray(i)
                    add(
                        Candle(
                            openTime = k.getLong(0),
                            open = k.getString(1).toDouble(),
                            high = k.getString(2).toDouble(),
                            low = k.getString(3).toDouble(),
                            close = k.getString(4).toDouble(),
                            closeTime = k.getLong(6),
                            quoteVolume = k.getString(7).toDouble(),
                            takerBuyQuote = k.getString(10).toDouble()
                        )
                    )
                }
            }
        }

    private fun get(url: String): String {
        val request = Request.Builder()
            .url(url)
            .header("User-Agent", "ScalpSignal-Android/0.1")
            .get()
            .build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("HTTP ${response.code}: ${response.message}")
            return response.body?.string() ?: throw IOException("Empty response")
        }
    }
}
