-- CUSTOM-0025: source-linked cells, custom scene pairing/arrival/trigger policy.
-- Proposal only. Host owns navigation, ownership, pending state and durable CAS.
local town_doors = require("gameplay.current_town_doors_data")
local island_boundaries = require("gameplay.current_island_boundaries_data")
local kunlun_doors = require("gameplay.current_kunlun_doors_data")
return {
    plan = function(input)
        if input.before_x == input.x and input.before_y == input.y then
            return nil
        end
        -- CUSTOM-0053: exact original mutual anchors. City only exposes point2;
        -- displaced movement activation and firstpoint0 landing are custom.
        -- Arrival cannot immediately bounce: a later displaced move is required.
        if input.area == 4 and input.allow_kunlun_parent then
            if input.scene == 3 and input.x == 50 and input.y == 124 then
                return {area=4,scene=0,x=318,y=363}
            end
            if input.scene == 0 and input.x == 318 and input.y == 363 then
                return {area=4,scene=3,x=50,y=124}
            end
        end
        if input.area == 4 and input.allow_kunlun_doors then
            for _,door in ipairs(kunlun_doors) do
                if input.scene == 3 and input.x == door[2] and input.y == door[3] then
                    return {area=4,scene=door[1],x=door[6],y=door[7]}
                end
                if input.scene == door[1] and input.x == door[8] and input.y == door[9] then
                    return {area=4,scene=3,x=door[4],y=door[5]}
                end
            end
        end
        if input.area ~= 2 then return nil end
        -- CUSTOM-0052: source point pairs, custom selector join/trigger policy.
        -- A point entry is active only with an explicit multi-scene registry.
        if input.allow_all_town_doors then
            for _, door in ipairs(town_doors) do
                if input.scene == 4 and input.x == door[2] and input.y == door[3] then
                    return {area=2, scene=door[1], x=door[6], y=door[7]}
                end
                if input.scene == door[1] and input.x == door[8] and input.y == door[9] then
                    return {area=2, scene=4, x=door[4], y=door[5]}
                end
            end
            -- CUSTOM-0036: the movement service checks these one-step source
            -- directions and the pinned full-boundary navigation before commit.
            if input.allow_island and (input.scene == 4 or input.scene == 0) then
                for _, edge in ipairs(island_boundaries) do
                    local offset = input.scene == 4 and 0 or 4
                    local tx,ty,ax,ay = edge[1+offset],edge[2+offset],edge[3+offset],edge[4+offset]
                    local aligned = (tx ~= ax and input.before_x == ax and math.abs(input.before_y-ty) <= 1) or
                                    (ty ~= ay and input.before_y == ay and math.abs(input.before_x-tx) <= 1)
                    if input.x == tx and input.y == ty and aligned then
                        if input.scene == 4 then
                            return {area=2,scene=0,x=edge[7],y=edge[8]}
                        end
                        return {area=2,scene=4,x=edge[3],y=edge[4]}
                    end
                end
            end
        end
        if input.scene == 4 and input.x == 86 and input.y == 70 then
            return { area = 2, scene = 15, x = 16, y = 19 }
        end
        if input.scene == 15 and input.x == 16 and input.y == 20 then
            return { area = 2, scene = 4, x = 86, y = 71 }
        end
        -- CUSTOM-0036: paired original model points; trigger/arrival policy is
        -- explicitly experimental until original-client streaming is proven.
        if input.allow_island then
            if input.scene == 4 and input.before_x == 56 and
               input.x == 55 and input.before_y == input.y and
               input.y >= 75 and input.y <= 80 then
                return { area = 2, scene = 0, x = 476, y = input.y + 134 }
            end
            if input.scene == 0 and input.before_x == 476 and
               input.x == 477 and
               input.before_y >= 209 and input.before_y <= 214 and
               math.abs(input.y - input.before_y) <= 1 and
               input.y >= 209 and input.y <= 214 then
                return { area = 2, scene = 4, x = 56, y = input.y - 134 }
            end
        end
        return nil
    end,
}
