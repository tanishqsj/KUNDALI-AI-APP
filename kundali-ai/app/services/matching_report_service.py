"""
Kundali Matching Report Service

Generates detailed interpretations for Ashta Koot matching factors.
"""

from typing import Dict, Any, Optional


class MatchingReportService:
    """
    Service to generate detailed text interpretations for Kundali matching.
    
    Based on traditional Vedic astrology interpretations for all 8 Koot factors.
    """

    # ─────────────────────────────────────────────
    # Interpretation Templates
    # ─────────────────────────────────────────────

    VARNA_INTERPRETATIONS = {
        ("Brahmin", "Brahmin"): "Both partners belong to the Brahmin varna, indicating a highly intellectual and spiritually aligned union. They share similar values regarding knowledge, wisdom, and dharmic pursuits. Their communication will be refined and they will understand each other's need for mental stimulation and higher learning.",
        ("Kshatriya", "Kshatriya"): "Both partners belong to the Kshatriya varna. They will have an understanding of feelings and moods, and have emotional harmony with each other. Both of them will have very good intuition for one another's thinking and thus, will be able to communicate on deeper layers of being. As far as home affairs are concerned, the natives will be very helpful and cooperating towards each other. Their understanding and hard work will lead them to greater achievements in life. This is a good alliance in all respects.",
        ("Vaishya", "Vaishya"): "Both partners belong to the Vaishya varna, suggesting compatibility in practical and business matters. They share similar values regarding commerce, prosperity, and material security. Together they can build a comfortable and prosperous household.",
        ("Shudra", "Shudra"): "Both partners belong to the Shudra varna, indicating compatibility in service-oriented and practical matters. They share similar approaches to work and daily life, leading to harmonious domestic arrangements.",
        "higher_boy": "The boy's varna is {boy_varna} and the girl comes under {girl_varna} varna. Since the boy's varna is equal or higher than the girl's, there will be natural respect and harmony in the relationship. The boy can provide guidance and the girl will be receptive, creating a balanced dynamic.",
        "lower_boy": "The boy's varna ({boy_varna}) is lower than the girl's ({girl_varna}). This may create some tension as traditional roles might feel reversed. However, with mutual respect and understanding, this can be overcome through conscious effort and appreciation of each other's strengths.",
    }

    VASHYA_INTERPRETATIONS = {
        ("Chatushpada", "Chatushpada"): "Both partners come under Chatushpad vashya. This pair indicates capability of achieving happiness, health and status together. There is good aspect of decent married life as both have a fair demand on each other on certain occasions. They encourage each other and mutual responsibility makes them loyal and attractive for each other. This combination comes out effectively in work and study and in matters related to diet, dress and personal hygiene. Both will have an emotional and a very soft-core for each other in their hearts. This is an excellent alliance for ceremonial marriage.",
        ("Manava", "Manava"): "Both partners belong to the Manava (Human) vashya. This indicates a balanced relationship where both partners understand human emotions, desires, and social dynamics. They will have natural empathy for each other and can communicate effectively about their needs and expectations.",
        ("Vanchar", "Vanchar"): "Both partners belong to the Vanchar (Wild/Forest) vashya. They share an independent and freedom-loving nature. Together they respect each other's need for personal space while maintaining a deep bond.",
        ("Jalchar", "Jalchar"): "Both partners belong to the Jalchar (Aquatic) vashya. They share emotional depth and intuitive understanding. Their relationship flows naturally, adapting to life's changes like water.",
        ("Keeta", "Keeta"): "Both partners belong to the Keeta (Insect/Reptile) vashya. They share resilience and the ability to adapt to challenging circumstances.",
        "compatible": "The boy belongs to {boy_vashya} vashya and the girl belongs to {girl_vashya} vashya. These vashyas have natural compatibility, indicating good mutual influence and understanding in the relationship.",
        "neutral": "The boy's vashya is {boy_vashya} and the girl's is {girl_vashya}. These vashyas have moderate compatibility. While there may be some differences in approach to life, with understanding and adjustment, they can create a harmonious relationship.",
        "incompatible": "The boy's vashya ({boy_vashya}) and the girl's vashya ({girl_vashya}) indicate some natural tension. One partner may feel more dominant while the other feels controlled. Conscious effort towards equality and mutual respect is essential.",
    }

    TARA_NAMES = {
        1: ("Janma", "Birth Star"),
        2: ("Sampat", "Wealth"),
        3: ("Vipat", "Danger"),
        4: ("Kshema", "Well-being"),
        5: ("Pratyari", "Obstacle"),
        6: ("Sadhaka", "Achievement"),
        7: ("Vadha", "Death/Obstruction"),
        8: ("Mitra", "Friend"),
        9: ("Ati-Mitra", "Great Friend"),
    }

    TARA_INTERPRETATIONS = {
        "auspicious": "The tara combination is auspicious (Tara {tara_num} - {tara_name}). This indicates favorable energy flow between the partners, supporting health, prosperity, and longevity of the relationship. They will naturally support each other's growth and well-being.",
        "neutral": "The tara combination is neutral (Tara {tara_num} - {tara_name}). The energy flow between partners is balanced. While not exceptionally favorable, it does not create obstacles either. The relationship can flourish with mutual effort.",
        "inauspicious": "The boy belongs to {boy_tara} tara while the girl belongs to {girl_tara} tara. According to the compatibility chart this is a normal union, not excellent and not even the worst. The energy flow may face some challenges. They may at times struggle to understand each other's perspectives. However, if other gunas are matched well, then this union may be taken into consideration with appropriate remedies.",
    }

    YONI_ANIMALS = {
        "Ashwa": "Horse", "Gaja": "Elephant", "Mesh": "Ram/Sheep", "Sarpa": "Serpent",
        "Shwan": "Dog", "Marjar": "Cat", "Mushak": "Rat", "Gow": "Cow",
        "Mahish": "Buffalo", "Vyaghra": "Tiger", "Mrig": "Deer", "Vanar": "Monkey",
        "Nakul": "Mongoose", "Simha": "Lion"
    }

    YONI_INTERPRETATIONS = {
        "same": "Both partners share the same yoni ({yoni}), indicating excellent physical and intimate compatibility. They understand each other's physical needs intuitively and share similar approaches to intimacy and physical expression of love.",
        "friendly": "The boy belongs to {boy_yoni} yoni while the girl belongs to {girl_yoni} yoni. A beneficial and very agreeable combination. The natives believe in working as 'we' and their help and support to each other work in their favor. The girl will be loyal and affectionate to the boy while he is the great strategist that she will be immensely proud of. The relationship flows in such a manner as to create mutual respect and increase in love for each other. Overall a very supportive, encouraging and charming match, physically as well as mentally.",
        "neutral": "The boy's yoni is {boy_yoni} and the girl's is {girl_yoni}. These yonis have neutral compatibility. Physical intimacy will require understanding and adjustment as both may have different approaches. With communication and patience, they can develop a satisfying physical relationship.",
        "enemy": "The boy's yoni ({boy_yoni}) and the girl's yoni ({girl_yoni}) are considered inimical. This may create challenges in physical compatibility and intimacy. However, with deep love, understanding, and conscious effort to bridge differences, these challenges can be addressed.",
    }

    GRAHA_MAITRI_INTERPRETATIONS = {
        "same_lord": "The boy and the girl both belong to the rasi lord {lord}. This combination is regarded very good by Vedic astrologers. They will be able to complement each other well and achieve long term relationship goals. He will be ambitious and she will be full of energy to support him. They will understand psychic and emotional needs of each other and will support each other. The boy is artistic and romantic, while the girl will prove as the source of life energy. This combination does increase the overall compatibility in the charts.",
        "friends": "The boy's moon sign is ruled by {boy_lord} and the girl's by {girl_lord}. These planetary lords are natural friends. This indicates excellent mental compatibility and understanding. They will think alike on important matters and support each other's goals and aspirations.",
        "neutral": "The boy's moon sign lord ({boy_lord}) and the girl's ({girl_lord}) have a neutral relationship. Mental compatibility is average. While they may not always see eye to eye, they can develop understanding through communication and shared experiences.",
        "enemies": "The boy's moon sign is ruled by {boy_lord} and the girl's by {girl_lord}. These lords are natural enemies. This may create fundamental differences in thinking and approach to life. However, with awareness and effort to appreciate different perspectives, they can still build a meaningful relationship.",
    }

    GANA_INTERPRETATIONS = {
        ("Deva", "Deva"): "Both partners belong to Deva gana (Divine temperament). They are naturally kind, charitable, and spiritually inclined. Their relationship will be marked by mutual respect, compassion, and a shared interest in higher pursuits.",
        ("Manushya", "Manushya"): "Both partners belong to Manushya gana (Human temperament). They are balanced, practical, and can navigate life's ups and downs with equanimity. Their relationship will be grounded in reality with healthy ambitions.",
        ("Rakshasa", "Rakshasa"): "Both partners belong to Rakshasa gana. Despite the name, this indicates strong willpower and determination. They understand each other's intensity and can channel their combined energy towards achieving great things.",
        ("Deva", "Manushya"): "The combination of Deva and Manushya gana is generally favorable. The divine qualities complement the practical human nature, creating a balanced relationship.",
        ("Manushya", "Deva"): "The combination of Manushya and Deva gana is generally favorable. The practical nature balances the spiritual inclinations.",
        ("Rakshasa", "Manushya"): "The boy belongs to Rakshasa gan and the girl belongs to Manushya gan. This combination has not been regarded as ideal by the sages. This combination may be characterized by aggression and over-domination. They may try to control each other and not provide enough emotional space. They may not be ready to listen and understand each other and may opt for aggressive and emotional methods to fulfill their demands. In this combination, the girl should not be influenced by others and should behave naturally. The boy should try to understand the girl's physical and emotional needs and act accordingly.",
        ("Manushya", "Rakshasa"): "The combination of Manushya and Rakshasa gana requires understanding. The Manushya partner should understand the intensity of the Rakshasa partner, while the Rakshasa partner should moderate their approach.",
        ("Deva", "Rakshasa"): "The combination of Deva and Rakshasa gana is traditionally considered challenging. Their fundamental natures differ significantly. However, with conscious effort and mutual respect, they can learn from each other's strengths.",
        ("Rakshasa", "Deva"): "The combination of Rakshasa and Deva gana is traditionally considered challenging. The Rakshasa partner may need to temper their intensity, while the Deva partner should try to understand the strength that underlies the Rakshasa nature.",
    }

    BHAKOOT_INTERPRETATIONS = {
        "same_sign": "The boy and the girl both come under {sign} sign. Same sign shows very good understanding between them. It shows love and harmony. Their family life will be full of joy and happiness. Both will have a great zest for life. They will find each other attractive physically as well as mentally.",
        "good": "The boy's moon sign is {boy_sign} and the girl's is {girl_sign}. The position of these signs relative to each other (distance: {distance}) is favorable for love, prosperity, and family happiness. They will support each other in building wealth and raising a family.",
        "bad": "The boy's moon sign ({boy_sign}) and the girl's ({girl_sign}) form a Bhakoot dosha (distance: {distance}). This may create challenges in areas of health, finances, or family matters. However, this dosha can be neutralized if the same lord rules both signs or if other factors are strongly favorable.",
    }

    NADI_INTERPRETATIONS = {
        "different": "The boy's nadi is {boy_nadi} and the girl comes under {girl_nadi} nadi. From nadi viewpoint, it is considered a very good combination. Natives will be very kind, spiritual in nature and fountain of compassion toward others. Their alliance will be on the spiritual level and they will love each other from the bottom of their hearts. They will have religious tilt of mind and prove to be a good team in social, cultural and charitable pursuits. They will be quite open to each other and will help to boost the other in their respective career.",
        "same": "Both partners have the same nadi ({nadi}). This is traditionally considered Nadi Dosha and is given significant importance. The same nadi may indicate similar constitutional types which could affect progeny and health matters. However, many couples with the same nadi lead happy lives. Remedial measures like Nadi Nivarana Puja are recommended. If other factors are strongly favorable, this can be mitigated.",
    }

    VERDICT_DESCRIPTIONS = {
        "Excellent Match": "This is an exceptional cosmic union! The stars strongly favor this alliance. Both partners complement each other beautifully across all dimensions - physical, emotional, mental, and spiritual. This relationship has the potential for deep love, mutual growth, and lasting happiness.",
        "Good Match": "This is a favorable alliance with strong compatibility in most areas. The partners will find natural harmony and understanding in their relationship. While some areas may require adjustment, the overall energy supports a successful and happy union.",
        "Average Match": "This is a moderate match with both strengths and areas that need attention. The partners can build a good relationship with conscious effort, understanding, and willingness to work on differences. Communication and compromise will be key to success.",
        "Below Average": "This match presents some challenges that require careful consideration. While not impossible, this union would require significant effort, understanding, and possibly remedial measures. The partners should discuss concerns openly and consider seeking guidance.",
    }

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def build_matching_report(
        self,
        match_data: Dict[str, Any],
        boy_name: str = "Boy",
        girl_name: str = "Girl",
    ) -> Dict[str, Any]:
        """
        Build a comprehensive matching report with detailed interpretations.
        
        Args:
            match_data: The match result from MatchingService.calculate_ashta_koot()
            boy_name: Name of the boy
            girl_name: Name of the girl
            
        Returns:
            Dict with all interpretations and original data
        """
        factors = match_data.get("factors", [])
        interpretations = {}
        
        for factor in factors:
            name = factor.get("name", "")
            boy_value = factor.get("boy_value", "")
            girl_value = factor.get("girl_value", "")
            score = factor.get("score", 0)
            max_score = factor.get("max", 0)
            
            if name == "Varna":
                interpretations["varna"] = self._get_varna_interpretation(
                    boy_value, girl_value, score
                )
            elif name == "Vashya":
                interpretations["vasya"] = self._get_vashya_interpretation(
                    boy_value, girl_value, score
                )
            elif name == "Tara":
                interpretations["tara"] = self._get_tara_interpretation(
                    boy_value, girl_value, score
                )
            elif name == "Yoni":
                interpretations["yoni"] = self._get_yoni_interpretation(
                    boy_value, girl_value, score
                )
            elif name == "Graha Maitri":
                interpretations["rasi_lord"] = self._get_graha_maitri_interpretation(
                    boy_value, girl_value, score
                )
            elif name == "Gana":
                interpretations["gana"] = self._get_gana_interpretation(
                    boy_value, girl_value, score
                )
            elif name == "Bhakoot":
                interpretations["bhakoot"] = self._get_bhakoot_interpretation(
                    boy_value, girl_value, score, match_data
                )
            elif name == "Nadi":
                interpretations["nadi"] = self._get_nadi_interpretation(
                    boy_value, girl_value, score
                )
        
        verdict = match_data.get("verdict", "Average Match")
        
        return {
            "match_id": match_data.get("match_id"),
            "boy_name": boy_name,
            "girl_name": girl_name,
            "total_score": match_data.get("total_score", 0),
            "max_score": match_data.get("max_score", 36),
            "percentage": match_data.get("percentage", 0),
            "verdict": verdict,
            "verdict_description": self.VERDICT_DESCRIPTIONS.get(
                verdict, self.VERDICT_DESCRIPTIONS["Average Match"]
            ),
            "interpretation": interpretations,
            "factors": factors,
        }

    # ─────────────────────────────────────────────
    # Private Interpretation Methods
    # ─────────────────────────────────────────────

    def _get_varna_interpretation(
        self, boy_varna: str, girl_varna: str, score: float
    ) -> str:
        """Get Varna interpretation."""
        key = (boy_varna, girl_varna)
        if key in self.VARNA_INTERPRETATIONS:
            return self.VARNA_INTERPRETATIONS[key]
        
        if score >= 1:
            return self.VARNA_INTERPRETATIONS["higher_boy"].format(
                boy_varna=boy_varna, girl_varna=girl_varna
            )
        else:
            return self.VARNA_INTERPRETATIONS["lower_boy"].format(
                boy_varna=boy_varna, girl_varna=girl_varna
            )

    def _get_vashya_interpretation(
        self, boy_vashya: str, girl_vashya: str, score: float
    ) -> str:
        """Get Vashya interpretation."""
        # Normalize names (remove 'a' suffix variations)
        boy_v = boy_vashya.replace("pada", "").strip() if boy_vashya else ""
        girl_v = girl_vashya.replace("pada", "").strip() if girl_vashya else ""
        
        key = (boy_v, girl_v)
        if key in self.VASHYA_INTERPRETATIONS:
            return self.VASHYA_INTERPRETATIONS[key]
        
        # Check reverse
        if (girl_v, boy_v) in self.VASHYA_INTERPRETATIONS:
            return self.VASHYA_INTERPRETATIONS[(girl_v, boy_v)]
        
        if score >= 2:
            return self.VASHYA_INTERPRETATIONS["compatible"].format(
                boy_vashya=boy_vashya, girl_vashya=girl_vashya
            )
        elif score >= 1:
            return self.VASHYA_INTERPRETATIONS["neutral"].format(
                boy_vashya=boy_vashya, girl_vashya=girl_vashya
            )
        else:
            return self.VASHYA_INTERPRETATIONS["incompatible"].format(
                boy_vashya=boy_vashya, girl_vashya=girl_vashya
            )

    def _get_tara_interpretation(
        self, boy_nakshatra: str, girl_nakshatra: str, score: float
    ) -> str:
        """Get Tara interpretation."""
        if score >= 3:
            tara_num = 3  # Auspicious tara
            tara_info = self.TARA_NAMES.get(tara_num, ("", ""))
            return self.TARA_INTERPRETATIONS["auspicious"].format(
                tara_num=tara_num, tara_name=tara_info[0]
            )
        elif score >= 1.5:
            tara_num = 4  # Neutral
            tara_info = self.TARA_NAMES.get(tara_num, ("", ""))
            return self.TARA_INTERPRETATIONS["neutral"].format(
                tara_num=tara_num, tara_name=tara_info[0]
            )
        else:
            return self.TARA_INTERPRETATIONS["inauspicious"].format(
                boy_tara="Janma", girl_tara="Vipat"
            )

    def _get_yoni_interpretation(
        self, boy_yoni: str, girl_yoni: str, score: float
    ) -> str:
        """Get Yoni interpretation."""
        if boy_yoni == girl_yoni:
            return self.YONI_INTERPRETATIONS["same"].format(yoni=boy_yoni)
        
        if score >= 3:
            return self.YONI_INTERPRETATIONS["friendly"].format(
                boy_yoni=boy_yoni, girl_yoni=girl_yoni
            )
        elif score >= 2:
            return self.YONI_INTERPRETATIONS["neutral"].format(
                boy_yoni=boy_yoni, girl_yoni=girl_yoni
            )
        else:
            return self.YONI_INTERPRETATIONS["enemy"].format(
                boy_yoni=boy_yoni, girl_yoni=girl_yoni
            )

    def _get_graha_maitri_interpretation(
        self, boy_lord: str, girl_lord: str, score: float
    ) -> str:
        """Get Graha Maitri (Rasi Lord) interpretation."""
        if boy_lord == girl_lord:
            return self.GRAHA_MAITRI_INTERPRETATIONS["same_lord"].format(lord=boy_lord)
        
        if score >= 5:
            return self.GRAHA_MAITRI_INTERPRETATIONS["friends"].format(
                boy_lord=boy_lord, girl_lord=girl_lord
            )
        elif score >= 3:
            return self.GRAHA_MAITRI_INTERPRETATIONS["neutral"].format(
                boy_lord=boy_lord, girl_lord=girl_lord
            )
        else:
            return self.GRAHA_MAITRI_INTERPRETATIONS["enemies"].format(
                boy_lord=boy_lord, girl_lord=girl_lord
            )

    def _get_gana_interpretation(
        self, boy_gana: str, girl_gana: str, score: float
    ) -> str:
        """Get Gana interpretation."""
        key = (boy_gana, girl_gana)
        if key in self.GANA_INTERPRETATIONS:
            return self.GANA_INTERPRETATIONS[key]
        
        # Try reverse
        if (girl_gana, boy_gana) in self.GANA_INTERPRETATIONS:
            return self.GANA_INTERPRETATIONS[(girl_gana, boy_gana)]
        
        # Default based on score
        if score >= 5:
            return f"The boy belongs to {boy_gana} gana and the girl to {girl_gana} gana. This is a favorable combination indicating compatible temperaments and natural understanding."
        elif score >= 3:
            return f"The boy's gana is {boy_gana} and the girl's is {girl_gana}. This is a moderate combination. Some adjustment in temperaments may be needed for harmony."
        else:
            return f"The combination of {boy_gana} and {girl_gana} gana requires attention. Different temperaments may lead to misunderstandings. Patience and communication are essential."

    def _get_bhakoot_interpretation(
        self, boy_sign: str, girl_sign: str, score: float, match_data: Dict
    ) -> str:
        """Get Bhakoot interpretation."""
        if boy_sign == girl_sign:
            return self.BHAKOOT_INTERPRETATIONS["same_sign"].format(sign=boy_sign)
        
        if score >= 7:
            return self.BHAKOOT_INTERPRETATIONS["good"].format(
                boy_sign=boy_sign, girl_sign=girl_sign, distance="favorable"
            )
        else:
            return self.BHAKOOT_INTERPRETATIONS["bad"].format(
                boy_sign=boy_sign, girl_sign=girl_sign, distance="6/8 or 2/12"
            )

    def _get_nadi_interpretation(
        self, boy_nadi: str, girl_nadi: str, score: float
    ) -> str:
        """Get Nadi interpretation."""
        if boy_nadi == girl_nadi:
            return self.NADI_INTERPRETATIONS["same"].format(nadi=boy_nadi)
        else:
            return self.NADI_INTERPRETATIONS["different"].format(
                boy_nadi=boy_nadi, girl_nadi=girl_nadi
            )

    def format_text_report(self, report: Dict[str, Any]) -> str:
        """
        Format the report as a plain text string.
        
        Args:
            report: The report dict from build_matching_report()
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("KUNDALI MATCHING REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Partners: {report['boy_name']} & {report['girl_name']}")
        lines.append(f"Total Score: {report['total_score']} / {report['max_score']} ({report['percentage']}%)")
        lines.append(f"Verdict: {report['verdict']}")
        lines.append("")
        lines.append("-" * 60)
        lines.append("INTERPRETATION")
        lines.append("-" * 60)
        lines.append("")
        
        # Factor names in order
        factor_order = [
            ("varna", "Varna"),
            ("vasya", "Vasya"),
            ("tara", "Tara"),
            ("yoni", "Yoni"),
            ("rasi_lord", "Rasi Lord"),
            ("gana", "Gana"),
            ("bhakoot", "Bhakoot"),
            ("nadi", "Nadi"),
        ]
        
        interpretations = report.get("interpretation", {})
        for key, name in factor_order:
            if key in interpretations:
                lines.append(f"## {name}")
                lines.append(interpretations[key])
                lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
