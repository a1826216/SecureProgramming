#include <iostream>
#include <string>
#include <utility>
#include <nlohmann/json.hpp>
#include <openssl/rsa.h>
 
class Client {
  private:
    unsigned int counter;

    // Work out how to do RSA keys with OpenSSL

    void send_hello();

  public:
      Client();
};
