import asyncio

async def echo(reader, writer):
    me = "{}:{}".format(*writer.get_extra_info('peername'))
    print(me)
    while data := await reader.readline():
        command = data.split()
        match command:
            case [b"print", *tail]:
                writer.write(b" ".join(tail))
            case [b"info", b"host"]:
                writer.write(writer.get_extra_info('peername')[0].encode())
            case [b"info", b"port"]:
                writer.write(str(writer.writer.get_extra_info('peername')[1].encode()))
            case _:
                writer.write(b"UNKNOWN COMMAND")
        writer.write(b"\n")
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(echo, '0.0.0.0', 1337)
    async with server:
        await server.serve_forever()

asyncio.run(main())

