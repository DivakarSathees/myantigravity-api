using System;
using System.Threading;

namespace PacMan
{
    public class Game
    {
        private Map map;
        private Player player;
        private Ghost ghost;
        private Renderer renderer;
        private InputHandler input;
        private bool running;

        public Game()
        {
            map = new Map();
            player = new Player(map.StartX, map.StartY);
            ghost = new Ghost(map.GhostX, map.GhostY);
            renderer = new Renderer(map, player, ghost);
            input = new InputHandler();
            running = true;
        }

        public void Run()
        {
            const int targetFps = 10;
            var frameTime = TimeSpan.FromMilliseconds(1000 / targetFps);

            while (running)
            {
                var frameStart = DateTime.UtcNow;

                HandleInput();
                Update();
                renderer.Render();

                if (map.PelletCount == 0)
                {
                    renderer.RenderWin();
                    break;
                }

                var elapsed = DateTime.UtcNow - frameStart;
                var sleep = frameTime - elapsed;
                if (sleep > TimeSpan.Zero)
                    Thread.Sleep(sleep);
            }

            renderer.RenderGameOver();
            input.Stop();
        }

        private void HandleInput()
        {
            var key = input.GetLastKey();
            if (key == ConsoleKey.Escape) running = false;

            if (key == ConsoleKey.UpArrow || key == ConsoleKey.W)
                player.SetDirection(0, -1);
            else if (key == ConsoleKey.DownArrow || key == ConsoleKey.S)
                player.SetDirection(0, 1);
            else if (key == ConsoleKey.LeftArrow || key == ConsoleKey.A)
                player.SetDirection(-1, 0);
            else if (key == ConsoleKey.RightArrow || key == ConsoleKey.D)
                player.SetDirection(1, 0);
        }

        private void Update()
        {
            player.Update(map);
            ghost.Update(map, player);

            if (player.X == ghost.X && player.Y == ghost.Y)
            {
                running = false; // caught
            }
        }
    }
}
