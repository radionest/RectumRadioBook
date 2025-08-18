"""Configuration module for image processing using pydantic-settings"""

from typing import Dict, List, Any
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import tomli


class InkscapeConfig(BaseModel):
    """Inkscape configuration"""
    executable: str = "inkscape"
    default_dpi: int = 300
    default_export_format: str = "png"


class ProcessingConfig(BaseModel):
    """Processing configuration"""
    default_style_file: str = "annotation.css"
    default_folder: str = "./img"
    annotation_patterns: List[str] = Field(default_factory=lambda: [
        "annotation.svg",
        "annotation_mri.svg",
        "annotation_ct.svg",
        "annotatiom_mri.svg",
        "annotation_anal_canal.svg"
         
    ])
    styled_postfix: str = "styled"
    annotated_suffix: str = "annotated"
    max_processes: int = 16


class ExportConfig(BaseModel):
    """Export configuration"""
    export_with_context: bool = True
    export_id_only: bool = True


class StyleConfig(BaseModel):
    """Individual style configuration"""
    fill: str
    stroke: str
    stroke_opacity: float = Field(ge=0, le=1)
    stroke_width: str


class Settings(BaseSettings):
    """Main settings class"""
    
    inkscape: InkscapeConfig = Field(default_factory=InkscapeConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    style_defaults: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    namespaces: Dict[str, str] = Field(default_factory=dict)
    
    model_config = SettingsConfigDict(
        env_prefix="PREPARE_IMAGES_",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    @classmethod
    def from_toml(cls, config_path: Path) -> "Settings":
        """Load settings from TOML file"""
        if not config_path.exists():
            return cls()
        
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)
        
        return cls(**config_data)
    
    def get_nsmap(self) -> Dict[str, str]:
        """Get namespace map with default values if not configured"""
        default_namespaces = {
            'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
            'cc': 'http://web.resource.org/cc/',
            'svg': 'http://www.w3.org/2000/svg',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'xlink': 'http://www.w3.org/1999/xlink',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
        }
        return self.namespaces or default_namespaces
    
    def get_default_styles(self) -> Dict[str, Dict[str, Any]]:
        """Get default styles with fallback values"""
        if self.style_defaults:
            return self.style_defaults
        
        return {
            'mucosa': {
                "fill": "#ffe5b4",
                "stroke": "none",
                "stroke-opacity": 1,
                "stroke-width": '3px'
            },
            'Слой 1': {
                "fill": "none",
                "stroke": "#000000",
                "stroke-opacity": 1,
                "stroke-width": '3px'
            }
        }


def load_config(config_file: str = "config.toml") -> Settings:
    """Load configuration from TOML file in styles directory"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / 'styles' / config_file
    
    return Settings.from_toml(config_path)