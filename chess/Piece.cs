using System;

namespace ChessApp
{
    public enum Color { White, Black }

    public abstract class Piece
    {
        public Color Color { get; }
        public abstract string Symbol { get; }

        protected Piece(Color color) => Color = color;

        protected string WhiteOrBlack(string white, string black)
        {
            return Color == Color.White ? white : black;
        }
    }

    public class Pawn : Piece
    {
        public Pawn(Color color) : base(color) { }
        public override string Symbol => WhiteOrBlack("♙", "♟");
    }

    public class Rook : Piece
    {
        public Rook(Color color) : base(color) { }
        public override string Symbol => WhiteOrBlack("♖", "♜");
    }
    

    public class Knight : Piece
    {
        public Knight(Color color) : base(color) { }
        public override string Symbol => WhiteOrBlack("♘", "♞");
    }

    public class Bishop : Piece
    {
        public Bishop(Color color) : base(color) { }
        public override string Symbol => WhiteOrBlack("♗", "♝");
    }

    public class Queen : Piece
    {
        public Queen(Color color) : base(color) { }
        public override string Symbol => WhiteOrBlack("♕", "♛");
    }

    public class King : Piece
    {
        public King(Color color) : base(color) { }
        public override string Symbol => WhiteOrBlack("♔", "♚");
    }
}
