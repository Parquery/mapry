#include <chrono>
#include <iostream>
#include <regex>
#include <string>

const std::regex kDuration(
  "^P(((0|[1-9][0-9]*)(\\.[0-9]+)?)Y)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)M)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)W)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)D)?"
  "(T"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)H)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)M)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)S)?"
  ")?$");

void print_match(bool matched, const std::smatch& mtch, const std::string& s) {
    std::cout << "String: " << s << std::endl;

    if(not matched) {
        std::cerr << "Failed to match the regular expression." << std::endl;
        return;
    }

    std::cout << "Match size: " << mtch.size() << std::endl;

    for(size_t i = 0; i < mtch.size(); ++i) {
        const auto& grp = mtch[i];

        std::cout << "Match " << i << ": " << grp << std::endl;
    }

    const double years = (mtch[2].length() == 0) ? 0.0 : std::stod(mtch[2]);
    const double months = (mtch[6].length() == 0) ? 0.0 : std::stod(mtch[6]);
    const double weeks = (mtch[10].length() == 0) ? 0.0 : std::stod(mtch[10]);
    const double days = (mtch[14].length() == 0) ? 0.0 : std::stod(mtch[14]);
    const double hours = (mtch[19].length() == 0) ? 0.0 : std::stod(mtch[19]);
    const double minutes  = (mtch[23].length() == 0) ? 0.0 : std::stod(mtch[23]);
    const double seconds = (mtch[27].length() == 0) ? 0.0 : std::stod(mtch[27]);

    std::cout << "years: " << years << std::endl;
    std::cout << "months: " << months << std::endl;
    std::cout << "weeks: " << weeks << std::endl;
    std::cout << "days: " << days << std::endl;
    std::cout << "hours: " << hours << std::endl;
    std::cout << "minutes: " << minutes << std::endl;
    std::cout << "seconds: " << seconds << std::endl;

    std::chrono::nanoseconds nanos(
        static_cast<int64_t>(
            years * 3.1536e+16 +
            months * 2.592e+15 +
            weeks * 6.048e+14 +
            days * 8.64e+13 +
            hours * 3.6e12 +
            minutes * 6e10 +
            seconds * 1e9));

    std::cout << "nanosecond count: " << nanos.count() << std::endl;
}

int main() {
    // everything
    const std::string s1 = "P1.1Y2.2M3.3W4.4DT5.5H6.6M7.7S";

    std::smatch mtch1;
    const bool matched1 = std::regex_match(s1, mtch1, kDuration);
    print_match(matched1, mtch1, s1);

    // only time
    const std::string s2 = "PT5.5H6.6M7.7S";

    std::smatch mtch2;
    const bool matched2 = std::regex_match(s2, mtch2, kDuration);
    print_match(matched2, mtch2, s2);

    // only non-time
    const std::string s3 = "P1.1Y2.2M3.3W4.4D";

    std::smatch mtch3;
    const bool matched3 = std::regex_match(s3, mtch3, kDuration);
    print_match(matched3, mtch3, s3);

    return 0;
}
