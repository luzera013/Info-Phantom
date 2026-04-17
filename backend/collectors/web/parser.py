"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Data Parser
Extrai dados estruturados de conteúdo web
"""

import re
import json
import time
from typing import Dict, Any, List, Set, Optional, Union
from dataclasses import dataclass
import logging
from urllib.parse import urlparse
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ExtractedData:
    """Dados extraídos do conteúdo"""
    emails: List[str] = None
    phones: List[str] = None
    names: List[str] = None
    links: List[str] = None
    social_links: List[str] = None
    addresses: List[str] = None
    companies: List[str] = None
    keywords: List[str] = None
    entities: List[str] = None
    numbers: List[str] = None
    dates: List[str] = None
    prices: List[str] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    
    def __post_init__(self):
        if self.emails is None:
            self.emails = []
        if self.phones is None:
            self.phones = []
        if self.names is None:
            self.names = []
        if self.links is None:
            self.links = []
        if self.social_links is None:
            self.social_links = []
        if self.addresses is None:
            self.addresses = []
        if self.companies is None:
            self.companies = []
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []
        if self.numbers is None:
            self.numbers = []
        if self.dates is None:
            self.dates = []
        if self.prices is None:
            self.prices = []
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []

class DataParser:
    """Parser avançado para extração de dados"""
    
    def __init__(self):
        self._compile_patterns()
        self._load_dictionaries()
        
        logger.info("🔍 Data Parser inicializado")
    
    def _compile_patterns(self):
        """Compila expressões regulares"""
        # Email patterns
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )
        
        # Phone patterns (internacional)
        self.phone_patterns = [
            # Brasil: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
            re.compile(r'\(\d{2}\)\s*\d{4,5}-\d{4}'),
            # US: XXX-XXX-XXXX
            re.compile(r'\d{3}-\d{3}-\d{4}'),
            # Internacional: +XX XXX XXXXXXX
            re.compile(r'\+\d{1,3}\s*\d{1,4}\s*\d{1,4}\s*\d{1,9}'),
            # Genérico: sequências de números com separadores
            re.compile(r'\b\d{2,4}[-.\s]\d{2,4}[-.\s]\d{4,}\b')
        ]
        
        # URL patterns
        self.url_pattern = re.compile(
            r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
            re.IGNORECASE
        )
        
        # Social media patterns
        self.social_patterns = {
            'facebook': re.compile(r'facebook\.com/[\w.]+', re.IGNORECASE),
            'twitter': re.compile(r'twitter\.com/[\w_]+', re.IGNORECASE),
            'instagram': re.compile(r'instagram\.com/[\w_.]+', re.IGNORECASE),
            'linkedin': re.compile(r'linkedin\.com/in/[\w-]+', re.IGNORECASE),
            'youtube': re.compile(r'youtube\.com/(?:user|channel)/[\w-]+', re.IGNORECASE),
            'github': re.compile(r'github\.com/[\w-]+', re.IGNORECASE),
            'tiktok': re.compile(r'tiktok\.com/@[\w.]+', re.IGNORECASE),
            'telegram': re.compile(r't\.me/[\w_]+', re.IGNORECASE),
            'whatsapp': re.compile(r'wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+', re.IGNORECASE)
        }
        
        # Price patterns
        self.price_patterns = [
            re.compile(r'R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?'),  # Brasil
            re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'),  # US
            re.compile(r'€\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?'),  # Euro
            re.compile(r'£\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')   # Libra
        ]
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'\d{1,2}/\d{1,2}/\d{4}'),  # DD/MM/YYYY
            re.compile(r'\d{4}-\d{2}-\d{2}'),     # YYYY-MM-DD
            re.compile(r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}', re.IGNORECASE),  # DD de Mês de YYYY
            re.compile(r'\w+\s+\d{1,2},?\s+\d{4}', re.IGNORECASE)  # Month DD, YYYY
        ]
        
        # Hashtag e mention patterns
        self.hashtag_pattern = re.compile(r'#\w+')
        self.mention_pattern = re.compile(r'@\w+')
        
        # CNPJ pattern (Brasil)
        self.cnpj_pattern = re.compile(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}')
        
        # CPF pattern (Brasil)
        self.cpf_pattern = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
        
        # CEP pattern (Brasil)
        self.cep_pattern = re.compile(r'\d{5}-\d{3}')
    
    def _load_dictionaries(self):
        """Carrega dicionários para reconhecimento de entidades"""
        # Nomes comuns em português
        self.common_names = {
            'joão', 'maria', 'josé', 'ana', 'carlos', 'pedro', 'paulo', 'lucas',
            'mateus', 'marcos', 'luiz', 'fernando', 'rodrigo', 'bruno', 'diego',
            'andre', 'ricardo', 'eduardo', 'gabriel', 'rafael', 'daniel', 'thiago',
            'mariana', 'camila', 'julia', 'beatriz', 'sophia', 'laura', 'valentina'
        }
        
        # Palavras-chave de negócios
        self.business_keywords = {
            'empresa', 'negócio', 'comércio', 'indústria', 'serviço', 'produto',
            'cliente', 'venda', 'compra', 'mercado', 'financeiro', 'contabilidade',
            'marketing', 'publicidade', 'tecnologia', 'inovação', 'desenvolvimento'
        }
        
        # Indicadores de endereço
        self.address_indicators = {
            'rua', 'avenida', 'alameda', 'travessa', 'praça', 'loteamento',
            'bairro', 'cidade', 'estado', 'país', 'cep', 'apartamento', 'casa',
            'sobrado', 'edifício', 'conjunto', 'bloco'
        }
    
    async def parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse completo do conteúdo
        
        Args:
            content: Texto para analisar
            
        Returns:
            Dicionário com dados extraídos
        """
        if not content:
            return {}
        
        logger.debug(f"🔍 Analisando conteúdo: {len(content)} caracteres")
        
        extracted = ExtractedData()
        
        # Extrair emails
        extracted.emails = self._extract_emails(content)
        
        # Extrair telefones
        extracted.phones = self._extract_phones(content)
        
        # Extrair nomes
        extracted.names = self._extract_names(content)
        
        # Extrair links
        extracted.links = self._extract_links(content)
        
        # Extrair links sociais
        extracted.social_links = self._extract_social_links(content)
        
        # Extrair endereços
        extracted.addresses = self._extract_addresses(content)
        
        # Extrair empresas
        extracted.companies = self._extract_companies(content)
        
        # Extrair palavras-chave
        extracted.keywords = self._extract_keywords(content)
        
        # Extrair entidades
        extracted.entities = self._extract_entities(content)
        
        # Extrair números
        extracted.numbers = self._extract_numbers(content)
        
        # Extrair datas
        extracted.dates = self._extract_dates(content)
        
        # Extrair preços
        extracted.prices = self._extract_prices(content)
        
        # Extrair hashtags
        extracted.hashtags = self._extract_hashtags(content)
        
        # Extrair menções
        extracted.mentions = self._extract_mentions(content)
        
        # Converter para dicionário
        result = {
            'emails': list(set(extracted.emails)),
            'phones': list(set(extracted.phones)),
            'names': list(set(extracted.names)),
            'links': list(set(extracted.links)),
            'social_links': list(set(extracted.social_links)),
            'addresses': list(set(extracted.addresses)),
            'companies': list(set(extracted.companies)),
            'keywords': list(set(extracted.keywords)),
            'entities': list(set(extracted.entities)),
            'numbers': list(set(extracted.numbers)),
            'dates': list(set(extracted.dates)),
            'prices': list(set(extracted.prices)),
            'hashtags': list(set(extracted.hashtags)),
            'mentions': list(set(extracted.mentions))
        }
        
        # Adicionar estatísticas
        result['stats'] = {
            'total_emails': len(result['emails']),
            'total_phones': len(result['phones']),
            'total_links': len(result['links']),
            'total_social_links': len(result['social_links']),
            'total_extractions': sum(len(v) for v in result.values() if isinstance(v, list))
        }
        
        logger.debug(f"✅ Extração concluída: {result['stats']['total_extractions']} itens")
        return result
    
    def _extract_emails(self, content: str) -> List[str]:
        """Extrai emails do conteúdo"""
        emails = self.email_pattern.findall(content)
        
        # Validar emails
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email.lower())
            except EmailNotValidError:
                continue
        
        return valid_emails
    
    def _extract_phones(self, content: str) -> List[str]:
        """Extrai telefones do conteúdo"""
        phones = set()
        
        for pattern in self.phone_patterns:
            matches = pattern.findall(content)
            phones.update(matches)
        
        # Validar com phonenumbers (se possível)
        valid_phones = []
        for phone in phones:
            # Limpar formato
            clean_phone = re.sub(r'[^\d+]', '', phone)
            if len(clean_phone) >= 10:  # Mínimo de 10 dígitos
                valid_phones.append(phone)
        
        return valid_phones
    
    def _extract_names(self, content: str) -> List[str]:
        """Extrai nomes do conteúdo"""
        # Extrair possíveis nomes (palavras que começam com maiúscula)
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        
        # Filtrar nomes comuns
        names = []
        for word in words:
            if word.lower() in self.common_names:
                names.append(word)
        
        return names
    
    def _extract_links(self, content: str) -> List[str]:
        """Extrai URLs do conteúdo"""
        links = self.url_pattern.findall(content)
        
        # Validar URLs
        valid_links = []
        for link in links:
            try:
                parsed = urlparse(link)
                if parsed.scheme in ['http', 'https'] and parsed.netloc:
                    valid_links.append(link)
            except:
                continue
        
        return valid_links
    
    def _extract_social_links(self, content: str) -> List[str]:
        """Extrai links de redes sociais"""
        social_links = []
        
        for platform, pattern in self.social_patterns.items():
            matches = pattern.findall(content)
            for match in matches:
                if not match.startswith('http'):
                    match = 'https://' + match
                social_links.append(match)
        
        return social_links
    
    def _extract_addresses(self, content: str) -> List[str]:
        """Extrai endereços do conteúdo"""
        addresses = []
        
        # Procurar padrões de endereço
        # CEP
        cep_matches = self.cep_pattern.findall(content)
        for cep in cep_matches:
            # Extrair contexto ao redor do CEP
            cep_index = content.find(cep)
            if cep_index != -1:
                start = max(0, cep_index - 100)
                end = min(len(content), cep_index + 100)
                context = content[start:end]
                addresses.append(context.strip())
        
        # Padrões com indicadores de endereço
        for indicator in self.address_indicators:
            pattern = rf'{indicator}\s+[^.,\n]+'
            matches = re.findall(pattern, content, re.IGNORECASE)
            addresses.extend(matches)
        
        return addresses
    
    def _extract_companies(self, content: str) -> List[str]:
        """Extrai nomes de empresas"""
        companies = []
        
        # CNPJ
        cnpj_matches = self.cnpj_pattern.findall(content)
        companies.extend(cnpj_matches)
        
        # Palavras seguidas de "Ltda", "S/A", etc.
        company_patterns = [
            r'\b[\w\s]+(?:Ltda|S\.A|ME|EPP)\b',
            r'\b[\w\s]+(?:Limitada|Sociedade Anônima)\b',
            r'\b[\w\s]+(?:Inc|Corp|LLC)\b'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            companies.extend(matches)
        
        return companies
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extrai palavras-chave relevantes"""
        keywords = []
        
        # Palavras de negócio
        for keyword in self.business_keywords:
            if keyword.lower() in content.lower():
                keywords.append(keyword)
        
        # Extrair termos em maiúscula (possíveis siglas/termos importantes)
        uppercase_words = re.findall(r'\b[A-Z]{2,}\b', content)
        keywords.extend(uppercase_words)
        
        return keywords
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extrai entidades nomeadas (simplificado)"""
        entities = []
        
        # CPF
        cpf_matches = self.cpf_pattern.findall(content)
        entities.extend(cpf_matches)
        
        # CNPJ
        cnpj_matches = self.cnpj_pattern.findall(content)
        entities.extend(cnpj_matches)
        
        # Placas de carro (Brasil)
        plate_pattern = re.compile(r'\b[A-Z]{3}\d{4}\b|\b[A-Z]{3}\d{1}[A-Z]\d{2}\b')
        plates = plate_pattern.findall(content)
        entities.extend(plates)
        
        return entities
    
    def _extract_numbers(self, content: str) -> List[str]:
        """Extrai números significativos"""
        # Extrair números com mais de 2 dígitos
        numbers = re.findall(r'\b\d{3,}\b', content)
        return numbers
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extrai datas do conteúdo"""
        dates = []
        
        for pattern in self.date_patterns:
            matches = pattern.findall(content)
            dates.extend(matches)
        
        return dates
    
    def _extract_prices(self, content: str) -> List[str]:
        """Extrai preços do conteúdo"""
        prices = []
        
        for pattern in self.price_patterns:
            matches = pattern.findall(content)
            prices.extend(matches)
        
        return prices
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extrai hashtags do conteúdo"""
        return self.hashtag_pattern.findall(content)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extrai menções do conteúdo"""
        return self.mention_pattern.findall(content)
    
    def extract_specific_type(self, content: str, data_type: str) -> List[str]:
        """
        Extrai um tipo específico de dado
        
        Args:
            content: Texto para analisar
            data_type: Tipo de dado (email, phone, name, etc.)
            
        Returns:
            Lista de dados extraídos
        """
        extractors = {
            'email': self._extract_emails,
            'phone': self._extract_phones,
            'name': self._extract_names,
            'link': self._extract_links,
            'social': self._extract_social_links,
            'address': self._extract_addresses,
            'company': self._extract_companies,
            'keyword': self._extract_keywords,
            'entity': self._extract_entities,
            'number': self._extract_numbers,
            'date': self._extract_dates,
            'price': self._extract_prices,
            'hashtag': self._extract_hashtags,
            'mention': self._extract_mentions
        }
        
        extractor = extractors.get(data_type.lower())
        if extractor:
            return extractor(content)
        
        return []
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e limpa dados extraídos
        
        Args:
            data: Dicionário de dados extraídos
            
        Returns:
            Dados validados
        """
        validated = {}
        
        for key, values in data.items():
            if isinstance(values, list):
                # Remover duplicatas e vazios
                cleaned = list(set(v for v in values if v and v.strip()))
                validated[key] = cleaned
            else:
                validated[key] = values
        
        return validated
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'web_parser',
            'timestamp': time.time(),
            'patterns_loaded': len(self.email_patterns) > 0,
            'validation_enabled': True
        }
