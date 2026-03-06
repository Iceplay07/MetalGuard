#include "analys_finance.h"
#include "result_finance.h"

bool Check_days(const std::vector<double>& price, int n){
    return price.size() >= n;
}

Signal Choose_signal(const AnalysisResult& result) {
    int buy_score = 0;
    int sell_score = 0;

    // BUY: актив дешевле своей короткой/средней нормы
    if (result.change_7d_per <= -1.5) {
        ++buy_score;
    }
    if (result.change_30d_per <= -1.0) {
        ++buy_score;
    }
    if (result.change_price_1d > 0) {
        ++buy_score;
    }
    if (result.change_ab_7d < 0) {
        ++buy_score;
    }
    if (result.change_nd_per <= -2.5) {
        ++buy_score;
    }

    // SELL: актив дороже своей короткой/средней нормы
    if (result.change_7d_per >= 1.5) {
        ++sell_score;
    }
    if (result.change_30d_per >= 1.0) {
        ++sell_score;
    }
    if (result.change_price_1d < 0) {
        ++sell_score;
    }
    if (result.change_ab_7d > 0) {
        ++sell_score;
    }
    if (result.change_nd_per >= 2.5) {
        ++sell_score;
    }

    bool buy_core =
        result.change_7d_per <= -1.5 &&
        result.change_30d_per <= -1.0 &&
        result.change_price_1d > 0;

    bool sell_core =
        result.change_7d_per >= 1.5 &&
        result.change_30d_per >= 1.0 &&
        result.change_price_1d < 0;

    if (buy_core && buy_score >= 3 && buy_score > sell_score) {
        return Signal::Buy;
    }

    if (sell_core && sell_score >= 3 && sell_score > buy_score) {
        return Signal::Sell;
    }

    return Signal::Hold;
}




AnalysisResult analyze(const std::vector<double>& price, int n){

    if (price.empty()) {
    return AnalysisResult{};
}

    bool check_n = Check_days(price, n);
    bool check_7 = Check_days(price, 7);
    bool check_30 = Check_days(price, 30);

    AnalysisResult result;
    result.price_today = price.back();
    result.change_price_1d = Change_price_about_1_days(price);


    if (check_n){
        result.average_nd = Average_price_n_days(price, n);
        result.change_av_nd = Change_price_n_days(price, n);
        result.change_ab_nd = Change_price_about_n_days(price, n);
        result.change_nd_per = Change_price_n_days_percent(price, n);
    }
    else{
        result.average_nd = 0;
        result.change_av_nd = 0;
        result.change_ab_nd = 0;
        result.change_nd_per = 0;
    }


    if (check_7){
        result.average_7d = Average_price_7_days(price);
        result.change_av_7d = Change_price_7_days(price);
        result.change_ab_7d = Change_price_about_7_days(price);
        result.change_7d_per = Change_price_7_days_percent(price);
    }
    else{
        result.average_7d = 0;
        result.change_av_7d = 0;
        result.change_ab_7d = 0;
        result.change_7d_per = 0;
    }


    if (check_30){
        result.average_30d = Average_price_30_days(price);
        result.change_av_30d = Change_price_30_days(price);
        result.change_ab_30d = Change_price_about_30_days(price);
        result.change_30d_per = Change_price_30_days_percent(price);
    }
    else{
        result.average_30d = 0;
        result.change_av_30d = 0;
        result.change_ab_30d = 0;
        result.change_30d_per = 0;
    }

    result.signal = Choose_signal(result);

    return result;

}