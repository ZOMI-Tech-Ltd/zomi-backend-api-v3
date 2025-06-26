from models.dish_profile import DishProfile


class FlavorTagService:
    """Service for generating user-friendly flavor tags from AI dish profiles"""
    
    BASIC_FLAVOR_MAP = {
        'basic_sweet': {'threshold': 0.4, 'tag': 'Sweet', 'emoji': '🍬', 'exclude': False},
        'basic_sour': {'threshold': 0.4, 'tag': 'Tangy', 'emoji': '🍋', 'exclude': False},
        'basic_salty': {'threshold': 0.4, 'tag': 'Salty', 'emoji': '🧂', 'exclude': False},
        'basic_spicy': {'threshold': 0.4, 'tag': 'Spicy', 'emoji': '🌶️', 'exclude': False},
        'basic_umami': {'threshold': 0.4, 'tag': 'Umami', 'emoji': '🍄', 'exclude': False},
        'basic_greasy': {'threshold': 0.4, 'tag': 'Rich', 'emoji': '🧈', 'exclude': False},
        'basic_fat_richness': {'threshold': 0.4, 'tag': 'Savory', 'emoji': '🥩', 'exclude': False},
        'basic_bitterness': {'threshold': 0.4, 'tag': 'Bitter', 'emoji': '☕', 'exclude': True},
        'basic_astringency': {'threshold': 0.4, 'tag': 'Astringent', 'emoji': '🍵', 'exclude': True},
    }
    
    DETAIL_FLAVOR_MAP = {
        'detail_smoky': {'threshold': 0.3, 'tag': 'Smoky', 'emoji': '🔥', 'exclude': False},
        'detail_roasted': {'threshold': 0.3, 'tag': 'Roasted', 'emoji': '🍗', 'exclude': False},
        'detail_caramelized': {'threshold': 0.3, 'tag': 'Caramelized', 'emoji': '🍯', 'exclude': False},
        'detail_fruity': {'threshold': 0.3, 'tag': 'Fruity', 'emoji': '🍓', 'exclude': False},
        'detail_floral': {'threshold': 0.3, 'tag': 'Floral', 'emoji': '🌸', 'exclude': False},
        'detail_herbal': {'threshold': 0.3, 'tag': 'Herbal', 'emoji': '🌿', 'exclude': False},
        'detail_spice_aroma': {'threshold': 0.3, 'tag': 'Spiced', 'emoji': '🧄', 'exclude': False},
        'detail_earthy': {'threshold': 0.3, 'tag': 'Earthy', 'emoji': '🍠', 'exclude': False},
        'detail_nutty': {'threshold': 0.3, 'tag': 'Nutty', 'emoji': '🥜', 'exclude': False},
        'detail_dairy': {'threshold': 0.3, 'tag': 'Milky', 'emoji': '🥛', 'exclude': False},
        'detail_fermented': {'threshold': 0.3, 'tag': 'Fermented', 'emoji': '🧫', 'exclude': False},
        'detail_meaty': {'threshold': 0.3, 'tag': 'Meaty', 'emoji': '🍖', 'exclude': False},
        'detail_marine': {'threshold': 0.3, 'tag': 'Ocean flavor', 'emoji': '🐟', 'exclude': False},
        'detail_peppery': {'threshold': 0.3, 'tag': 'Peppery', 'emoji': '🧂', 'exclude': False},
        'detail_citrusy': {'threshold': 0.3, 'tag': 'Citrusy', 'emoji': '🍊', 'exclude': False},
        'detail_toasty': {'threshold': 0.3, 'tag': 'Toasty', 'emoji': '🍞', 'exclude': False},
        # Excluded detail flavors
        'detail_medicinal': {'threshold': 0.3, 'tag': 'Medicinal', 'emoji': '💊', 'exclude': True},
        'detail_offal_gamey': {'threshold': 0.3, 'tag': 'Gamey', 'emoji': '🦌', 'exclude': True},
        'detail_sulfurous': {'threshold': 0.3, 'tag': 'Sulfurous', 'emoji': '🥚', 'exclude': True},
        'detail_burnt': {'threshold': 0.3, 'tag': 'Burnt', 'emoji': '🔥', 'exclude': True},
    }
    
    TEXTURE_MAP = {
        'texture_crispiness': {'threshold': 0.5, 'tag': 'Crispy', 'emoji': '🍘', 'exclude': False},
        'texture_crunchiness': {'threshold': 0.5, 'tag': 'Crunchy', 'emoji': '🍤', 'exclude': False},
        'texture_tenderness': {'threshold': 0.5, 'tag': 'Tender', 'emoji': '🥩', 'exclude': False},
        'texture_chewiness': {'threshold': 0.5, 'tag': 'Chewy', 'emoji': '🍬', 'exclude': False},
        'texture_springiness': {'threshold': 0.5, 'tag': 'Bouncy', 'emoji': '🥚', 'exclude': False},
        'texture_juiciness': {'threshold': 0.5, 'tag': 'Juicy', 'emoji': '🍑', 'exclude': False},
        'texture_moistness': {'threshold': 0.5, 'tag': 'Moist', 'emoji': '💧', 'exclude': False},
        'texture_creaminess': {'threshold': 0.5, 'tag': 'Creamy', 'emoji': '🍦', 'exclude': False},
        'texture_smoothness': {'threshold': 0.5, 'tag': 'Smooth', 'emoji': '🍮', 'exclude': False},
        # Excluded textures
        'texture_dryness': {'threshold': 0.5, 'tag': 'Dry', 'emoji': '🏜️', 'exclude': True},
        'texture_hardness': {'threshold': 0.5, 'tag': 'Hard', 'emoji': '🪨', 'exclude': True},
        'texture_stickiness': {'threshold': 0.5, 'tag': 'Sticky', 'emoji': '🍯', 'exclude': True},
    }
    
    COMBINED_FLAVOR_PATTERNS = [
        {
            'pattern': ['basic_sweet', 'basic_sour'],
            'threshold': 0.4,
            'tag': 'Sweet & Sour',
            'emoji': '🍬🍋',
            'priority': 1
        },
        {
            'pattern': ['basic_salty', 'basic_umami'],
            'threshold': 0.4,
            'tag': 'Savory & Salty',
            'emoji': '🧂🍄',
            'priority': 2
        },
        {
            'pattern': ['basic_spicy', 'basic_greasy'],
            'threshold': 0.4,
            'tag': 'Spicy & Rich',
            'emoji': '🌶️🧈',
            'priority': 1
        },
        {
            'pattern': ['detail_herbal', 'detail_citrusy'],
            'threshold': 0.3,
            'tag': 'Refreshing flavor',
            'emoji': '🌿🍊',
            'priority': 2
        },
        {
            'pattern': ['detail_caramelized', 'detail_roasted'],
            'threshold': 0.3,
            'tag': 'Charred sweetness',
            'emoji': '🍯🔥',
            'priority': 2
        }
    ]
    
    COMBINED_TEXTURE_PATTERNS = [
        {
            'pattern': ['texture_crispiness', 'texture_juiciness'],
            'threshold': 0.5,
            'tag': 'Crispy outside, juicy inside',
            'emoji': '🍘🍑',
            'priority': 1
        },
        {
            'pattern': ['texture_creaminess', 'texture_smoothness'],
            'threshold': 0.5,
            'tag': 'Melt-in-mouth',
            'emoji': '🍦🍮',
            'priority': 1
        },
        {
            'pattern': ['texture_stickiness', 'texture_chewiness'],
            'threshold': 0.5,
            'tag': 'Sticky & Chewy',
            'emoji': '🍡',
            'priority': 3
        }
    ]
    
    CUISINE_MAP = {
        'Japanese': {'tag': 'Japanese Cuisine', 'emoji': '🇯🇵'},
        'Chinese': {'tag': 'Chinese Cuisine', 'emoji': '🇨🇳'},
        'Korean': {'tag': 'Korean Cuisine', 'emoji': '🇰🇷'},
        'Thai': {'tag': 'Thai Cuisine', 'emoji': '🇹🇭'},
        'Vietnamese': {'tag': 'Vietnamese Cuisine', 'emoji': '🇻🇳'},
        'Italian': {'tag': 'Italian Cuisine', 'emoji': '🇮🇹'},
        'French': {'tag': 'French Cuisine', 'emoji': '🇫🇷'},
        'Indian': {'tag': 'Indian Cuisine', 'emoji': '🇮🇳'},
        'Mexican': {'tag': 'Mexican Cuisine', 'emoji': '🇲🇽'},
        'Mediterranean': {'tag': 'Mediterranean', 'emoji': '🫒'},
        'American': {'tag': 'American Cuisine', 'emoji': '🇺🇸'},
    }
    
    @classmethod
    def generate_flavor_tags(cls, dish_profile: DishProfile, max_tags: int = 5) -> list:
        """
        Generate 3-5 user-friendly flavor tags from dish profile data
        
        Args:
            dish_profile: DishProfile object with AI-generated scores
            max_tags: Maximum number of tags to return (default 5)
            
        Returns:
            List of tag dictionaries with 'text', 'emoji', 'category', 'priority'
        """
        if not dish_profile:
            return []
        
        tags = []
        
        # 1. Check for combined patterns first (higher priority)
        combined_tags = cls._get_combined_tags(dish_profile)
        tags.extend(combined_tags)
        
        # 2. Get individual flavor tags
        if len(tags) < max_tags:
            individual_tags = cls._get_individual_tags(dish_profile, max_tags - len(tags))
            tags.extend(individual_tags)
        
        # 3. Add cuisine tag if available and space permits
        if len(tags) < max_tags and dish_profile.background_cuisine:
            cuisine_tag = cls._get_cuisine_tag(dish_profile.background_cuisine)
            if cuisine_tag:
                tags.append(cuisine_tag)
        
        # 4. Sort by priority and return top tags
        tags.sort(key=lambda x: x.get('priority', 99))
        return tags[:max_tags]
    
    @classmethod
    def _get_combined_tags(cls, dish_profile: DishProfile) -> list:
        """Check for combined flavor/texture patterns"""
        tags = []
        
        # Check combined flavor patterns
        for pattern in cls.COMBINED_FLAVOR_PATTERNS:
            if cls._pattern_matches(dish_profile, pattern):
                tags.append({
                    'text': pattern['tag'],
                    'emoji': pattern['emoji'],
                    'category': 'combined_flavor',
                    'priority': pattern['priority']
                })
        
        # Check combined texture patterns
        for pattern in cls.COMBINED_TEXTURE_PATTERNS:
            if cls._pattern_matches(dish_profile, pattern):
                tags.append({
                    'text': pattern['tag'],
                    'emoji': pattern['emoji'],
                    'category': 'combined_texture',
                    'priority': pattern['priority']
                })
        
        return tags
    
    @classmethod
    def _pattern_matches(cls, dish_profile: DishProfile, pattern: dict) -> bool:
        """Check if a combined pattern matches the dish profile"""
        for field in pattern['pattern']:
            value = getattr(dish_profile, field, 0) or 0
            if value < pattern['threshold']:
                return False
        return True
    
    @classmethod
    def _get_individual_tags(cls, dish_profile: DishProfile, max_tags: int) -> list:
        """Get individual flavor, detail, and texture tags"""
        tag_candidates = []
        
        # Basic flavors
        for field, config in cls.BASIC_FLAVOR_MAP.items():
            if config['exclude']:
                continue
            value = getattr(dish_profile, field, 0) or 0
            if value >= config['threshold']:
                tag_candidates.append({
                    'text': config['tag'],
                    'emoji': config['emoji'],
                    'category': 'basic_flavor',
                    'priority': 2,
                    'score': value
                })
        
        # Detail flavors
        for field, config in cls.DETAIL_FLAVOR_MAP.items():
            if config['exclude']:
                continue
            value = getattr(dish_profile, field, 0) or 0
            if value >= config['threshold']:
                tag_candidates.append({
                    'text': config['tag'],
                    'emoji': config['emoji'],
                    'category': 'detail_flavor',
                    'priority': 2,
                    'score': value
                })
        
        # Textures (limit to 1-2 to avoid overwhelming)
        texture_tags = []
        for field, config in cls.TEXTURE_MAP.items():
            if config['exclude']:
                continue
            value = getattr(dish_profile, field, 0) or 0
            if value >= config['threshold']:
                texture_tags.append({
                    'text': config['tag'],
                    'emoji': config['emoji'],
                    'category': 'texture',
                    'priority': 3,
                    'score': value
                })
        
        # Sort texture tags by score and take top 2
        texture_tags.sort(key=lambda x: x['score'], reverse=True)
        tag_candidates.extend(texture_tags[:2])
        
        # Sort all candidates by score and priority
        tag_candidates.sort(key=lambda x: (x['priority'], -x['score']))
        
        return tag_candidates[:max_tags]
    
    @classmethod
    def _get_cuisine_tag(cls, cuisine: str) -> dict:
        """Get cuisine tag with appropriate emoji"""
        if not cuisine:
            return None
        
        # Try exact match first
        if cuisine in cls.CUISINE_MAP:
            config = cls.CUISINE_MAP[cuisine]
            return {
                'text': config['tag'],
                'emoji': config['emoji'],
                'category': 'cuisine',
                'priority': 4
            }
        
        # Try partial match
        cuisine_lower = cuisine.lower()
        for key, config in cls.CUISINE_MAP.items():
            if key.lower() in cuisine_lower:
                return {
                    'text': config['tag'],
                    'emoji': config['emoji'],
                    'category': 'cuisine',
                    'priority': 4
                }
        
        # Default cuisine tag without emoji
        return {
            'text': f"{cuisine} Cuisine",
            'emoji': '🍽️',
            'category': 'cuisine',
            'priority': 4
        }
    
    @classmethod
    def format_tags_for_display(cls, tags: list) -> list:
        """Format tags for API response with emoji integration"""
        formatted_tags = []
        
        for tag in tags:
            # Create display text with emoji
            display_text = f"{tag['emoji']} {tag['text']}" if tag.get('emoji') else tag['text']
            
            formatted_tags.append({
                'text': display_text,
                'category': tag.get('category', 'flavor'),
                'raw_text': tag['text'],
                'emoji': tag.get('emoji', '')
            })
        
        return formatted_tags