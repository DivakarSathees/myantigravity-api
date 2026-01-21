namespace ChessConsole
{
    public class Rook : Piece
    {
        public Rook(PieceColor color) : base(color) { }
        public override string WhiteSymbol => "♖";
        public override string BlackSymbol => "♜";
    }
}
