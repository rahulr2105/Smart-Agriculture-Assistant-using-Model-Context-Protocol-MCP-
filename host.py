import asyncio

from fastmcp import Client

from config import SERVERS


async def main():

    client = Client(SERVERS)

    async with client:

        print("=" * 60)
        print("Connected Successfully")
        print("=" * 60)

        print("\nAvailable Tools\n")

        tools = await client.list_tools()

        for tool in tools:
            print(f"• {tool.name}")

        print("\n")

        while True:

            print("=" * 60)
            tool = input("Tool Name (exit to quit): ")

            if tool == "exit":
                break

            args = {}

            while True:

                key = input("Parameter Name (blank to finish): ")

                if key == "":
                    break

                value = input(f"Value for {key}: ")

                args[key] = value

            print("\nCalling Tool...\n")

            result = await client.call_tool(tool, args)

            print(result.text)

            print()


if __name__ == "__main__":
    asyncio.run(main())