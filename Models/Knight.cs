namespace ChessConsole
{
    public class Knight : Piece
    {
        public Knight(PieceColor color) : base(color) { }
        public override string WhiteSymbol => "♘";
        public override string BlackSymbol => "♞";
    }
}
