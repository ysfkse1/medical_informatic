def language_processor(request):
    """Tüm template'lere language değişkenini ekler"""
    return {
        'language': request.session.get('language', 'tr')
    }
