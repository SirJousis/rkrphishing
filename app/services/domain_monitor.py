import socket
import itertools

class DomainMonitorService:
    @staticmethod
    def generate_variations(domain):
        """
        Generates common typosquatting variations for a given domain.
        """
        parts = domain.split('.')
        if len(parts) < 2:
            return []
        
        name = parts[0]
        tld = '.'.join(parts[1:])
        
        variations = set()
        
        # 1. Common TLDs
        common_tlds = ['com', 'net', 'org', 'info', 'biz', 'io', 'co', 'online']
        for ext in common_tlds:
            if ext != tld:
                variations.add(f"{name}.{ext}")
        
        # 2. Character Omission
        for i in range(len(name)):
            variations.add(f"{name[:i]}{name[i+1:]}.{tld}")
        
        # 3. Character Swapping (Adjacent)
        for i in range(len(name) - 1):
            swapped = list(name)
            swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
            variations.add(f"{''.join(swapped)}.{tld}")
            
        # 4. Common Character Substitutions (Homoglyphs - simplified)
        substitutions = {
            'a': ['4', 'o'],
            'e': ['3'],
            'i': ['1', 'l'],
            'o': ['0', 'a'],
            's': ['5'],
            't': ['7']
        }
        for i, char in enumerate(name):
            if char in substitutions:
                for sub in substitutions[char]:
                    variations.add(f"{name[:i]}{sub}{name[i+1:]}.{tld}")
        
        # 5. Adding common prefixes/suffixes
        prefixes = ['login-', 'secure-', 'verify-', 'update-']
        suffixes = ['-login', '-secure', '-support']
        for p in prefixes:
            variations.add(f"{p}{name}.{tld}")
        for s in suffixes:
            variations.add(f"{name}{s}.{tld}")

        # Remove the original domain if it was added
        if domain in variations:
            variations.remove(domain)
            
        return list(variations)

    @staticmethod
    def is_registered(domain):
        """
        Checks if a domain is registered by trying to resolve its IP.
        """
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False

    @classmethod
    def scan_domain(cls, monitored_domain_obj):
        """
        Scans for variations of a monitored domain and returns newly discovered ones.
        """
        from app.models.discovered_domain import DiscoveredDomain
        from app.extensions import db
        
        variations = cls.generate_variations(monitored_domain_obj.domain)
        discovered = []
        
        for variation in variations:
            # Check if it exists in the wild
            if cls.is_registered(variation):
                # Check if we already discovered it
                existing = DiscoveredDomain.query.filter_by(
                    monitored_domain_id=monitored_domain_obj.id,
                    domain=variation
                ).first()
                
                if not existing:
                    new_discovery = DiscoveredDomain(
                        monitored_domain_id=monitored_domain_obj.id,
                        domain=variation,
                        status="potential"
                    )
                    db.session.add(new_discovery)
                    discovered.append(new_discovery)
        
        if discovered:
            db.session.commit()
            
        return discovered
