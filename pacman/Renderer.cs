using System;

namespace PacMan
{
    public class Renderer
    {
        private Map map;
        private Player player;
        private Ghost ghost;

        public Renderer(Map map, Player player, Ghost ghost)
        {
            this.map = map;
            this.player = player;
            this.ghost = ghost;
            Console.Clear();
        }

        public void Render()
        {
            Console.SetCursorPosition(0,0);
            for (int y = 0; y < map.Height; y++)
            {
                for (int x = 0; x < map.Width; x++)
                {
                    if (x == player.X && y == player.Y)
                    {
                        Console.ForegroundColor = ConsoleColor.Yellow;
                        Console.Write('P');
                        Console.ResetColor();
                    }
                    else if (x == ghost.X && y == ghost.Y)
                    {
                        Console.ForegroundColor = ConsoleColor.Red;
                        Console.Write('G');
                        Console.ResetColor();
                    }
                    else
                    {
                        var t = map.GetTile(x, y);
                        if (t == '#') Console.Write('█');
                        else if (t == '.') Console.Write('.');
                        else Console.Write(' ');
                    }
                }
                Console.WriteLine();
            }
            Console.WriteLine("Use arrow keys or WASD to move. Esc to quit.");
            Console.WriteLine($"Pellets remaining: {map.PelletCount}");
        }

        public void RenderGameOver()
        {
            Console.SetCursorPosition(0, map.Height + 3);
            Console.WriteLine("Game Over. Press any key to exit...");
            Console.ReadKey(true);
        }

        public void RenderWin()
        {
            Console.SetCursorPosition(0, map.Height + 3);
            Console.WriteLine("You Win! All pellets collected. Press any key to exit...");
            Console.ReadKey(true);
        }
    }
}
