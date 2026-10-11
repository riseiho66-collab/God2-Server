#pragma once
#include <stdexcept>
namespace god2 {
class DatabaseError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};
class UnsupportedDatabaseError : public DatabaseError {
public:
    using DatabaseError::DatabaseError;
};
}
