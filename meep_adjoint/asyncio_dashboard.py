

######################################################################
######################################################################
######################################################################
import asyncio
dashboard_sock, dashboard_task = None, None

async def async_run_dashboard(sock):
    return run_dashboard(sock)

async def async_launch_dashboard():
    global dashboard_sock, dashboard_task
    sp = socket.socketpair()
    dashboard_sock = sp[0]
    dashboard_task = asyncio.create_task(async_run_dashboard(sp[1]))


def howdage():
    asyncio.run(async_launch_dashboard())
