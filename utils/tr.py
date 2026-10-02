# بدلاً من استيراد translation_manager مباشرة، سنستخدم متغيرًا عالميًا
_translation_manager = None

def set_translation_manager(manager):
    """تعيين مدير الترجمة بعد إنشائه"""
    global _translation_manager
    _translation_manager = manager

def tr(key, default=None):
    """وظيفة الترجمة الرئيسية"""
    if _translation_manager is None:
        return default if default is not None else key
    
    # محاولة الحصول على الترجمة من مدير الترجمة
    translation = _translation_manager.translate(key)
    
    # إذا لم تكن هناك ترجمة، نعيد القيمة الافتراضية إن وجدت أو المفتاح نفسه
    if translation:
        return translation
    return default if default is not None else key