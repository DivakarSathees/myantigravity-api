using System;

class Program
{
    static void Main(string[] args)
    {
        int size = 10; // default size
        if (args.Length > 0)
        {
            if (!int.TryParse(args[0], out size) || size <= 0)
            {
                Console.WriteLine("Invalid size argument. Using default size 10.");
                size = 10;
            }
        }

        // Print header
        Console.Write("    ");
        for (int c = 1; c <= size; c++)
        {
            Console.Write($"{c,4}");
        }
        Console.WriteLine();

        // Separator
        Console.Write("    ");
        for (int c = 1; c <= size; c++) Console.Write("----");
        Console.WriteLine();

        // Rows
        for (int r = 1; r <= size; r++)
        {
            Console.Write($"{r,3} | ");
            for (int c = 1; c <= size; c++)
            {
                Console.Write($"{r * c,4}");
            }
            Console.WriteLine();
        }
    }
}
