#pragma once
#include "core/Config.h"
namespace god2 {
struct WebServerPlan;
struct SharedWorldHostPlan;
struct TaiwanThreeChannelPlan;
int run_server(const Config& config, unsigned run_for_seconds=0);
// Explicit web opt-in uses only Taiwan listeners hosted in this Application lifetime.
int run_server(const Config&,const WebServerPlan&,unsigned run_for_seconds=0);
// Explicit world source hosting requires the actual Taiwan scene owner.
int run_server(const Config&,const SharedWorldHostPlan&,unsigned run_for_seconds=0);
int run_server(const Config&,const WebServerPlan&,const SharedWorldHostPlan&,unsigned run_for_seconds=0);
// Actual three native source cohorts; supplied complete sources, never labels.
int run_server(const Config&,const TaiwanThreeChannelPlan&,unsigned run_for_seconds=0);
int run_server(const Config&,const WebServerPlan&,const TaiwanThreeChannelPlan&,unsigned run_for_seconds=0);
}
