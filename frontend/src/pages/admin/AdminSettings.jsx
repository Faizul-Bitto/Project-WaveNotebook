import { useEffect, useState } from 'react';
import { FaSave } from 'react-icons/fa';
import { adminGetSettings, adminUpdateSettings } from '../../api/adminServices';
import { useSiteSettings } from '../../context/SiteSettingsContext';

function AdminSettings () {
    const { refresh } = useSiteSettings();
    const [ siteName, setSiteName ] = useState( 'WaveNotebook' );
    const [ logoUrl, setLogoUrl ] = useState( '' );
    const [ logoFile, setLogoFile ] = useState( null );
    const [ saving, setSaving ] = useState( false );
    const [ error, setError ] = useState( null );
    const [ success, setSuccess ] = useState( null );

    useEffect( () => {
        const loadSettings = async () => {
            try {
                const data = await adminGetSettings();
                const s = data.settings || {};
                setSiteName( s.site_name || 'WaveNotebook' );
                setLogoUrl( s.logo_url || '' );
            } catch ( err ) {
                setError( err.response?.data?.detail || 'Failed to load settings.' );
            }
        };
        loadSettings();
    }, [] );

    const handleLogoChange = ( e ) => {
        const file = e.target.files[ 0 ];
        if ( file ) {
            setLogoFile( file );
            setLogoUrl( URL.createObjectURL( file ) );
        }
    };

    const handleSubmit = async ( e ) => {
        e.preventDefault();
        setError( null );
        setSuccess( null );
        try {
            setSaving( true );
            const formData = new FormData();
            formData.append( 'site_name', siteName );
            if ( logoFile ) formData.append( 'logo', logoFile );
            await adminUpdateSettings( formData );
            await refresh();
            setSuccess( 'Settings saved successfully! Logo updated.' );
        } catch ( err ) {
            setError( err.response?.data?.detail || 'Failed to save settings.' );
        } finally {
            setSaving( false );
        }
    };

    return (
        <div className="admin-page">
            <h2>Site Settings</h2>
            { error && <div className="alert alert-error">{ error }</div> }
            { success && <div className="alert alert-success">{ success }</div> }

            <form onSubmit={ handleSubmit }>
                <div className="order-detail-card">
                    <h3>Logo & Branding</h3>

                    { logoUrl && (
                        <div style={ { marginBottom: '16px', textAlign: 'center' } }>
                            <img
                                src={ logoUrl }
                                alt="Site Logo"
                                style={ { height: '60px', maxWidth: '200px', objectFit: 'contain', background: '#f3f4f6', padding: '8px', borderRadius: '8px' } }
                            />
                        </div>
                    ) }

                    <div className="form-group">
                        <label>Site Name</label>
                        <input type="text" value={ siteName } onChange={ ( e ) => setSiteName( e.target.value ) } placeholder="WaveNotebook" />
                    </div>

                    <div className="form-group">
                        <label>Upload Logo</label>
                        <input type="file" accept="image/*" onChange={ handleLogoChange } />
                        <p className="upload-hint">Upload a logo (PNG, JPG)</p>
                    </div>

                    <button type="submit" className="btn btn-primary" disabled={ saving }>
                        <FaSave /> { saving ? 'Saving...' : 'Save Settings' }
                    </button>
                </div>
            </form>
        </div>
    );
}

export default AdminSettings;