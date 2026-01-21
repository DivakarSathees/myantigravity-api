using System;
using System.Linq;

namespace ChessApp
{
    public class Board
    {
        public Piece?[,] Squares { get; } = new Piece[8,8];

        public void SetupInitialPosition()
        {
            // Clear
            for (int r = 0; r < 8; r++)
                for (int f = 0; f < 8; f++)
                    Squares[r,f] = null;

            // Pawns
            for (int f = 0; f < 8; f++)
            {
                Squares[1,f] = new Pawn(Color.Black);
                Squares[6,f] = new Pawn(Color.White);
            }

            // Rooks
            Squares[0,0] = new Rook(Color.Black);
            Squares[0,7] = new Rook(Color.Black);
            Squares[7,0] = new Rook(Color.White);
            Squares[7,7] = new Rook(Color.White);

            // Knights
            Squares[0,1] = new Knight(Color.Black);
            Squares[0,6] = new Knight(Color.Black);
            Squares[7,1] = new Knight(Color.White);
            Squares[7,6] = new Knight(Color.White);

            // Bishops
            Squares[0,2] = new Bishop(Color.Black);
            Squares[0,5] = new Bishop(Color.Black);
            Squares[7,2] = new Bishop(Color.White);
            Squares[7,5] = new Bishop(Color.White);

            // Queens
            Squares[0,3] = new Queen(Color.Black);
            Squares[7,3] = new Queen(Color.White);

            // Kings
            Squares[0,4] = new King(Color.Black);
            Squares[7,4] = new King(Color.White);
        }

        public void Print()
        {
            Console.WriteLine("  a b c d e f g h");
            for (int r = 0; r < 8; r++)
            {
                int rank = 8 - r;
                Console.Write(rank + " ");
                for (int f = 0; f < 8; f++)
                {
                    var piece = Squares[r,f];
                    if (piece == null)
                    {
                        // draw square color background maybe not supported everywhere; fallback to dot
                        Console.Write(((r + f) % 2 == 0) ? "·" : ":");
                    }
                    else
                    {
                        Console.Write(piece.Symbol);
                    }
                    Console.Write(' ');
                }
                Console.WriteLine(" " + rank);
            }
            Console.WriteLine("  a b c d e f g h");
        }
    }
}
