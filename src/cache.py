import asyncio 


tournament_cache = { 
    #server_id: [(db_id,tournament name),....]
}

tournament_cache_timers = {

}

async def set_cache(cache,server_id,data):
    cache[server_id] = data
    return data

async def reset_cache(cache,server_id):
    cache[server_id] = None

async def start_cache_timer(cache,server_id):
    await asyncio.sleep(600)
    await reset_cache(cache,server_id)

    pass

async def clear_all_cache(cache):
    cache = {}
    pass

async def get_cache_data(cache,server_id):
    return cache[server_id] 