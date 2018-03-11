#include <ctime>
#include <iostream>

int main() {
    // ctime
    struct tm dtime = tm{0};

    std::cout <<
        dtime.tm_year + 1900 << "-" << dtime.tm_mon + 1 << "-" << dtime.tm_mday << "T" <<
            dtime.tm_hour << ":" << dtime.tm_min << ":" << dtime.tm_sec << std::endl;

    return 0;
}
