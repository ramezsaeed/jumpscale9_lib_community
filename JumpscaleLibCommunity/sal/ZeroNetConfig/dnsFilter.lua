local key = ARGV[1]

local lasttime=0



if redis.call("HEXISTS", "eco:objects",key)==1 then
    local ecoraw=redis.call("HGET", "eco:objects",key)
    local ecodb=cjson.decode(ecoraw)
    eco["occurrences"]=ecodb["occurrences"]+1
    lasttime = ecodb["lasttime"]
    eco["lasttime"]=eco["epoch"]
    eco["epoch"]=ecodb["epoch"]
    eco["guid"]=ecodb["guid"]
else
    eco["occurrences"]=1
    eco["lasttime"]=eco["epoch"]

end

local ecoraw=cjson.encode(eco)

redis.call("HSET", "eco:objects",key,ecoraw)

if lasttime<(eco["lasttime"]-300) then
    --more than 5 min ago
    redis.call("RPUSH", "queues:eco",key)
end

if redis.call("LLEN", "queues:eco") > 1000 then
    local todelete = redis.call("LPOP", "queues:eco")
    redis.call("HDEL","eco:objects",todelete)
end

if redis.call("HLEN", "eco:objects") > 1000 then
    redis.call("DEL", "eco:objects")
end


return ecoraw
