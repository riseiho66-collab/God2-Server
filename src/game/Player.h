#pragma once
#include "game/Entity.h"
#include "game/Character.h"
#include "net/Session.h"
#include "text/ChineseText.h"
#include <memory>
namespace god2 {
struct Player : Entity {
    Character character;
    std::weak_ptr<Session> session;
    // CUSTOM-0029: player display preference; character state remains untouched.
    ChineseLanguage text_language=ChineseLanguage::Traditional;
};
}
