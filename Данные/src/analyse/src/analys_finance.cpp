#include "analys_finance.h"


// average

double Average_price_n_days(const std::vector<double>& price, int days) {
    if (days <= 0 || price.size() < days) {
        return -1;
    }
    double result = 0.0;

    for (size_t i = price.size() - days; i < price.size(); ++i) {
        result += price[i];
    }

    return result / days;
}

double Average_price_7_days(const std::vector<double>& price) {
    return Average_price_n_days(price, 7);
}

double Average_price_30_days(const std::vector<double>& price) {
    return Average_price_n_days(price, 30);
}



// change price about average of days
double Change_price_n_days(const std::vector<double>& price, int days){
    double average_n_d = Average_price_n_days(price, days);
    if (average_n_d < 0) return -1;
    double result = price.back() - average_n_d;
    return result;
}

double Change_price_7_days(const std::vector<double>& price){
    return Change_price_n_days(price, 7);
}

double Change_price_30_days(const std::vector<double>& price){
    return Change_price_n_days(price, 30);
}


// change price about last day

double Change_price_about_n_days(const std::vector<double>& price, int days){

    if(price.size() < days) return -1;
    double result = price.back() - price[price.size() - days - 1];
    return result;
}

double Change_price_about_7_days(const std::vector<double>& price){

    return Change_price_about_n_days(price, 7);
}

double Change_price_about_30_days(const std::vector<double>& price){

    return Change_price_about_n_days(price, 30);
}

double Change_price_about_1_days(const std::vector<double>& price){
    return Change_price_about_n_days(price, 1);
}



// change price in percent

double Change_price_n_days_percent(const std::vector<double>& price, int days){
    double average_price = Average_price_n_days(price, days);
    double price_today = price.back();
    return ((price_today / average_price) - 1.0) * 100.0;
}

double Change_price_7_days_percent(const std::vector<double>& price){
    return Change_price_n_days_percent(price, 7);
}

double Change_price_30_days_percent(const std::vector<double>& price){
    return Change_price_n_days_percent(price, 30);
}