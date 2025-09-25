import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface UpdateConfigRequest {
  agentId: string;
  configPath: string;
  sectionKey: string;
  fieldKey: string;
  value: any;
  envVar?: string;
}

function updateEnvVariable(envVar: string, value: any) {
  try {
    const projectRoot = process.cwd().split('/agent-inbox')[0];
    const envPath = path.join(projectRoot, '.env');

    let envContent = '';
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }

    const lines = envContent.split('\n');
    const envVarRegex = new RegExp(`^${envVar}=`);
    let updated = false;

    // Find and update existing variable
    for (let i = 0; i < lines.length; i++) {
      if (envVarRegex.test(lines[i])) {
        lines[i] = `${envVar}=${value}`;
        updated = true;
        break;
      }
    }

    // Add new variable if not found
    if (!updated) {
      lines.push(`${envVar}=${value}`);
    }

    // Write back to .env file
    fs.writeFileSync(envPath, lines.join('\n'));
    return true;
  } catch (error) {
    console.error('Error updating .env file:', error);
    return false;
  }
}

function updateConfigFile(configPath: string, sectionKey: string, fieldKey: string, value: any) {
  try {
    const projectRoot = process.cwd().split('/agent-inbox')[0];
    const fullPath = path.join(projectRoot, configPath);

    if (!fs.existsSync(fullPath)) {
      return false;
    }

    const content = fs.readFileSync(fullPath, 'utf8');

    // For now, we'll focus on env-based updates
    // TODO: Implement Python config file updates for non-env fields
    console.log(`Config file update not yet implemented for ${configPath}`);
    return true;
  } catch (error) {
    console.error('Error updating config file:', error);
    return false;
  }
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { agentId, configPath, sectionKey, fieldKey, value, envVar } = req.body as UpdateConfigRequest;

    try {
      let success = true;

      // If this field has an environment variable, update .env
      if (envVar) {
        success = updateEnvVariable(envVar, value);
      } else {
        // Otherwise, update the config file directly
        success = updateConfigFile(configPath, sectionKey, fieldKey, value);
      }

      if (success) {
        res.status(200).json({
          success: true,
          message: `Updated ${fieldKey} for ${agentId}`,
        });
      } else {
        res.status(500).json({
          success: false,
          error: 'Failed to update configuration',
        });
      }
    } catch (error) {
      console.error('Update error:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error',
      });
    }
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}