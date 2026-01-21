using System;

class Program
{
    static void Main(string[] args)
    {
        int n;

        if (args.Length > 0 && int.TryParse(args[0], out n))
        {
            // use arg
        }
        else
        {
            Console.Write("Enter an odd positive integer for the diamond height (e.g., 7): ");
            var input = Console.ReadLine();
            if (!int.TryParse(input, out n))
            {
                Console.WriteLine("Invalid input. Using default 7.");
                n = 7;
            }
        }

        if (n <= 0)
        {
            Console.WriteLine("Number must be positive. Using default 7.");
            n = 7;
        }

        // Ensure n is odd
        if (n % 2 == 0)
        {
            Console.WriteLine($"{n} is even. Increasing to {n + 1} to make it odd.");
            n += 1;
        }

        PrintDiamond(n);
    }

    static void PrintDiamond(int n)
    {
        int mid = n / 2; // zero-based

        for (int i = 0; i <= mid; i++)
        {
            int stars = 2 * i + 1;
            int spaces = (n - stars) / 2;
            Console.Write(new string(' ', spaces));
            Console.WriteLine(new string('*', stars));
        }

        for (int i = mid - 1; i >= 0; i--)
        {
            int stars = 2 * i + 1;
            int spaces = (n - stars) / 2;
            Console.Write(new string(' ', spaces));
            Console.WriteLine(new string('*', stars));
        }
    }
}
