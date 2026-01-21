using System;
using System.Threading;

namespace PacMan
{
    public class InputHandler
    {
        private ConsoleKey lastKey = 0;
        private bool running = true;
        private Thread thread;

        public InputHandler()
        {
            thread = new Thread(Run) { IsBackground = true };
            thread.Start();
        }

        private void Run()
        {
            while (running)
            {
                if (Console.KeyAvailable)
                {
                    var k = Console.ReadKey(true).Key;
                    lastKey = k;
                }
                Thread.Sleep(10);
            }
        }

        public ConsoleKey GetLastKey()
        {
            var k = lastKey;
            lastKey = 0;
            return k;
        }

        public void Stop()
        {
            running = false;
            thread.Join(200);
        }
    }
}
