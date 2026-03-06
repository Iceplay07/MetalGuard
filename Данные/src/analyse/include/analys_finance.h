#ifndef ANALYS_FINANCE_H
#define ANALYS_FINANCE_H

#include <vector>

// =========================
// Average price functions
// =========================

// Возвращает среднюю цену за последние `days` дней.
// Если days <= 0 или данных меньше, чем days, возвращает -1.
double Average_price_n_days(const std::vector<double>& price, int days);

// Возвращает среднюю цену за последние 7 дней.
double Average_price_7_days(const std::vector<double>& price);

// Возвращает среднюю цену за последние 30 дней.
double Average_price_30_days(const std::vector<double>& price);


// ==========================================
// Change relative to average price functions
// ==========================================

// Возвращает абсолютное отклонение текущей цены от средней цены
// за последние `days` дней.
// Формула:
// current_price - average_price_n_days
double Change_price_n_days(const std::vector<double>& price, int days);

// Возвращает абсолютное отклонение текущей цены от средней за 7 дней.
double Change_price_7_days(const std::vector<double>& price);

// Возвращает абсолютное отклонение текущей цены от средней за 30 дней.
double Change_price_30_days(const std::vector<double>& price);


// ==========================================
// Change relative to price N days ago
// ==========================================

// Возвращает абсолютное изменение цены относительно цены `days` дней назад.
// Формула:
// current_price - price_n_days_ago
double Change_price_about_n_days(const std::vector<double>& price, int days);

// Возвращает абсолютное изменение цены относительно цены 7 дней назад.
double Change_price_about_7_days(const std::vector<double>& price);

// Возвращает абсолютное изменение цены относительно цены 30 дней назад.
double Change_price_about_30_days(const std::vector<double>& price);

// Возвращает абсолютное изменение цены относительно цены 1 день назад.
double Change_price_about_1_days(const std::vector<double>& price);


// ==========================================
// Percent change functions
// ==========================================

// Возвращает процентное отклонение текущей цены от средней цены
// за последние `days` дней.
// Формула:
// ((current_price / average_price) - 1.0) * 100.0
double Change_price_n_days_percent(const std::vector<double>& price, int days);

// Возвращает процентное отклонение текущей цены от средней за 7 дней.
double Change_price_7_days_percent(const std::vector<double>& price);

// Возвращает процентное отклонение текущей цены от средней за 30 дней.
double Change_price_30_days_percent(const std::vector<double>& price);

#endif // ANALYS_FINANCE_H