using System;

namespace PacMan
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.CursorVisible = false;
            var game = new Game();
            game.Run();
            Console.CursorVisible = true;
            Console.ResetColor();
        }
    }
}
