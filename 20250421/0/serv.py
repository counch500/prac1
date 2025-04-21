import asyncio
from func import sqroots

async def handle_equation(reader, writer):
    try:
        data = await reader.readline()
        equation = data.decode().strip()
        try:
            result = sqroots(equation)
        except:
            result = ""
        writer.write(f"{result}\n".encode())
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(
        handle_equation,
        '0.0.0.0',
        1337
    )
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
