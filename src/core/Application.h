#pragma once
#include "core/Config.h"
namespace god2 {
namespace cn {struct SharedServerPlan;}
struct WebServerPlan;
struct SharedWorldHostPlan;
int run_server(const Config& config, unsigned run_for_seconds=0);
// Explicit source hosting only: caller supplies the complete qualified native
// controllers. Existing production main/config never synthesizes a CN plan.
int run_server(const Config& config,const cn::SharedServerPlan&,unsigned run_for_seconds=0);
// Explicit web opt-in uses only listeners hosted in this Application lifetime.
int run_server(const Config&,const WebServerPlan&,unsigned run_for_seconds=0);
int run_server(const Config&,const cn::SharedServerPlan&,const WebServerPlan&,unsigned run_for_seconds=0);
// Explicit common-world source hosting; mandatory actual Taiwan scene owner.
int run_server(const Config&,const SharedWorldHostPlan&,unsigned run_for_seconds=0);
int run_server(const Config&,const cn::SharedServerPlan&,const SharedWorldHostPlan&,unsigned run_for_seconds=0);
int run_server(const Config&,const WebServerPlan&,const SharedWorldHostPlan&,unsigned run_for_seconds=0);
int run_server(const Config&,const cn::SharedServerPlan&,const WebServerPlan&,
               const SharedWorldHostPlan&,unsigned run_for_seconds=0);
}
