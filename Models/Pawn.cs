namespace ChessConsole
{
    public class Pawn : Piece
    {
        public Pawn(PieceColor color) : base(color) { }
        public override string WhiteSymbol => "♙";
        public override string BlackSymbol => "♟";
    }
}
