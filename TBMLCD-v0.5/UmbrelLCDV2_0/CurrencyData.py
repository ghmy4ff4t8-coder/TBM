import sys

# Currencies supported by CoinGecko API (fiat only, as of 2025)
# Source: https://api.coingecko.com/api/v3/simple/supported_vs_currencies
# Crypto/commodity pairs (BTC, ETH, XRP, etc.) excluded intentionally.
currencySymbols = {
    'AED': 'د.إ',   # UAE Dirham
    'ARS': '$',      # Argentine Peso
    'AUD': '$',      # Australian Dollar
    'BDT': '৳',      # Bangladeshi Taka
    'BHD': 'ب.د',    # Bahraini Dinar
    'BMD': '$',      # Bermudian Dollar
    'BRL': 'R$',     # Brazilian Real
    'CAD': '$',      # Canadian Dollar
    'CHF': 'Fr',     # Swiss Franc
    'CLP': '$',      # Chilean Peso
    'CNY': '¥',      # Chinese Yuan
    'CZK': 'Kč',     # Czech Koruna
    'DKK': 'kr',     # Danish Krone
    'EUR': '€',      # Euro
    'GBP': '£',      # British Pound
    'GEL': '₾',      # Georgian Lari
    'HKD': '$',      # Hong Kong Dollar
    'HUF': 'Ft',     # Hungarian Forint
    'IDR': 'Rp',     # Indonesian Rupiah
    'ILS': '₪',      # Israeli New Shekel
    'INR': '₹',      # Indian Rupee
    'JPY': '¥',      # Japanese Yen
    'KRW': '₩',      # South Korean Won
    'KWD': 'د.ك',    # Kuwaiti Dinar
    'LKR': 'Rs',     # Sri Lankan Rupee
    'MMK': 'K',      # Myanmar Kyat
    'MXN': '$',      # Mexican Peso
    'MYR': 'RM',     # Malaysian Ringgit
    'NGN': '₦',      # Nigerian Naira
    'NOK': 'kr',     # Norwegian Krone
    'NZD': '$',      # New Zealand Dollar
    'PHP': '₱',      # Philippine Peso
    'PKR': '₨',      # Pakistani Rupee
    'PLN': 'zł',     # Polish Zloty
    'RUB': '₽',      # Russian Ruble
    'SAR': 'ر.س',    # Saudi Riyal
    'SEK': 'kr',     # Swedish Krona
    'SGD': '$',      # Singapore Dollar
    'THB': '฿',      # Thai Baht
    'TRY': '₺',      # Turkish Lira
    'TWD': '$',      # New Taiwan Dollar
    'UAH': '₴',      # Ukrainian Hryvnia
    'USD': '$',      # US Dollar
    'VEF': 'Bs',     # Venezuelan Bolívar
    'VND': '₫',      # Vietnamese Dong
    'ZAR': 'R',      # South African Rand
}

# Main
if __name__ == '__main__':
    try:
        currency = sys.argv[1]
        currSymbol = currencySymbols[currency]
        print("Valid")
    except:
        print("Not Valid")
