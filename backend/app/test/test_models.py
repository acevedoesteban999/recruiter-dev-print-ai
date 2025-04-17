from app.models import BookModel
impofrort pytest

def test_book_model_valid():
    book = BookModel(
        title="Clean Code",
        price=29.99,
        category="Programming",
        image_url="http://example.com/img.jpg"
    )
    assert book.price > 0

def test_book_model_invalid():
    with pytest.raises(ValueError):
        BookModel(title="Bad Book", price=-10, category="Invalid")  # Precio negativo → error