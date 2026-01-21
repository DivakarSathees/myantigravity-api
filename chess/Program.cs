using System;

namespace ChessApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;

            var board = new Board();
            board.SetupInitialPosition();
            board.Print();

            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
    }
}
