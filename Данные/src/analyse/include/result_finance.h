#ifndef RESULT_FINANCE_H_
#define RESULT_FINANCE_H_

#include <iostream>
#include <vector>
#include <cmath>
#include <string>
#include <sstream>


enum class Signal {
    Buy,
    Hold,
    Sell
};


struct AnalysisResult
{
    double price_today;
    double change_price_1d;

    double average_7d;
    double change_av_7d;
    double change_ab_7d;
    double change_7d_per;

    double average_30d;
    double change_av_30d;
    double change_ab_30d;
    double change_30d_per;

    double average_nd;
    double change_av_nd;
    double change_ab_nd;
    double change_nd_per;

    Signal signal;
};

// Выполняет полный анализ временного ряда цен за период n
// и возвращает заполненную структуру AnalysisResult.
AnalysisResult analyze(const std::vector<double>& prices, int n);

// Выбирает торговый сигнал на основе рассчитанных показателей.
Signal Choose_signal(const AnalysisResult& result);

// Проверяет, хватает ли данных в векторе цен для анализа за n дней.
bool Check_days(const std::vector<double>& price, int n);





#endif