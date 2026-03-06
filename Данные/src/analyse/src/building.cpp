#include "analys_finance.h"
#include "result_finance.h"
#include <vector>

extern "C" {

struct CAnalysisResult {
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

    int signal; // 0 = Buy, 1 = Hold, 2 = Sell
};

int analyze_prices(const double* prices, int len, int n, CAnalysisResult* out) {
    if (!prices || len <= 0 || !out) {
        return 0;
    }

    std::vector<double> data(prices, prices + len);
    AnalysisResult r = analyze(data, n);

    out->price_today = r.price_today;
    out->change_price_1d = r.change_price_1d;

    out->average_7d = r.average_7d;
    out->change_av_7d = r.change_av_7d;
    out->change_ab_7d = r.change_ab_7d;
    out->change_7d_per = r.change_7d_per;

    out->average_30d = r.average_30d;
    out->change_av_30d = r.change_av_30d;
    out->change_ab_30d = r.change_ab_30d;
    out->change_30d_per = r.change_30d_per;

    out->average_nd = r.average_nd;
    out->change_av_nd = r.change_av_nd;
    out->change_ab_nd = r.change_ab_nd;
    out->change_nd_per = r.change_nd_per;

    out->signal = static_cast<int>(r.signal);

    return 1;
}

}